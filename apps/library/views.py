import csv
import logging
import re
from decimal import Decimal
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    AuthorForm,
    BookForm,
    BorrowForm,
    CategoryForm,
    FineForm,
    FinePaymentForm,
    MemberForm,
    NotificationForm,
    PublisherForm,
    ReportForm,
    ReturnForm,
    RoleForm,
    SupabaseAuthLoginForm,
    SupabaseAuthRegisterForm,
    UserCreateForm,
    UserUpdateForm,
)
from .models import (
    Author,
    Book,
    BorrowRecord,
    Category,
    Fine,
    Member,
    Notification,
    Publisher,
    Report,
    Role,
    User,
)
from .services.supabase_auth import SupabaseAuthError, get_supabase_auth_service

FINE_RATE_PER_DAY = Decimal("1.00")
LIST_PAGE_SIZE = 15
LOCAL_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"

audit_logger = logging.getLogger("library.audit")
error_logger = logging.getLogger("library.errors")


class LocalUserSyncError(Exception):
    """Raised when a Supabase identity cannot be mapped to a local user."""


def is_library_staff(user):
    """Return True when a user may access staff library workflows."""

    if not user.is_authenticated:
        return False
    return user.can_manage_library


staff_required = user_passes_test(is_library_staff, login_url="library:login")


ENTITY_CONFIG = {
    "roles": {
        "model": Role,
        "form": RoleForm,
        "title": "Roles",
        "headers": ["ID", "Role name", "Description"],
        "row": lambda item: [item.role_id, item.role_name, item.description or "-"],
    },
    "users": {
        "model": User,
        "create_form": UserCreateForm,
        "update_form": UserUpdateForm,
        "title": "Users",
        "headers": ["ID", "Username", "Full name", "Role", "Active"],
        "row": lambda item: [
            item.user_id,
            item.username,
            item.full_name,
            item.role.role_name,
            "Yes" if item.is_active else "No",
        ],
        "queryset": lambda: User.objects.select_related("role"),
    },
    "categories": {
        "model": Category,
        "form": CategoryForm,
        "title": "Categories",
        "headers": ["ID", "Category name", "Description"],
        "row": lambda item: [
            item.category_id,
            item.category_name,
            item.description or "-",
        ],
    },
    "authors": {
        "model": Author,
        "form": AuthorForm,
        "title": "Authors",
        "headers": ["ID", "Author name", "Biography"],
        "row": lambda item: [
            item.author_id,
            item.author_name,
            item.biography or "-",
        ],
    },
    "publishers": {
        "model": Publisher,
        "form": PublisherForm,
        "title": "Publishers",
        "headers": ["ID", "Publisher name", "Contact", "Email"],
        "row": lambda item: [
            item.publisher_id,
            item.publisher_name,
            item.contact_number or "-",
            item.email or "-",
        ],
    },
    "members": {
        "model": Member,
        "form": MemberForm,
        "title": "Members",
        "headers": ["ID", "Code", "Name", "Type", "Department", "Status"],
        "row": lambda item: [
            item.member_id,
            item.member_code,
            item.user.full_name,
            item.get_member_type_display(),
            item.department or "-",
            item.get_status_display(),
        ],
        "queryset": lambda: Member.objects.select_related("user"),
    },
}


def _entity_config(entity):
    try:
        return ENTITY_CONFIG[entity]
    except KeyError as exc:
        raise Http404("Unknown library data type.") from exc


def _entity_queryset(config):
    factory = config.get("queryset")
    return factory() if factory else config["model"].objects.all()


def _paginate(request, queryset, per_page=LIST_PAGE_SIZE):
    """Return a page object while tolerating invalid page numbers."""

    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _pagination_context(request, page_obj):
    params = request.GET.copy()
    params.pop("page", None)
    return {"page_obj": page_obj, "pagination_query": params.urlencode()}


def _sync_overdue_records():
    """Mark active loans overdue before dashboard/list calculations."""

    today = timezone.localdate()
    return BorrowRecord.objects.filter(
        status=BorrowRecord.BORROWED,
        due_date__lt=today,
        return_date__isnull=True,
    ).update(status=BorrowRecord.OVERDUE)


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return settings.LOGIN_REDIRECT_URL


def _store_supabase_session(request, identity):
    request.session[settings.SUPABASE_AUTH_SESSION_KEY] = {
        "user_id": identity.supabase_user_id,
        "email": identity.email,
        "access_token": identity.access_token,
        "refresh_token": identity.refresh_token,
    }


def _clear_supabase_session(request):
    request.session.pop(settings.SUPABASE_AUTH_SESSION_KEY, None)


def _validate_local_login_user(user):
    if not user.is_active:
        raise LocalUserSyncError("This local library account is inactive.")
    if not user.role_id:
        raise LocalUserSyncError(
            "This local library account has no role assigned. "
            "Please contact the library administrator."
        )
    return user


def _default_supabase_role():
    role = Role.objects.filter(
        role_name__iexact=settings.SUPABASE_AUTH_DEFAULT_ROLE
    ).first()
    if not role:
        raise LocalUserSyncError(
            f"Default role '{settings.SUPABASE_AUTH_DEFAULT_ROLE}' does not exist."
        )
    return role


def _username_from_email(email):
    base = re.sub(r"[^a-zA-Z0-9_.-]+", "_", email.split("@", 1)[0]).strip("._-")
    base = (base or "user")[:40]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        suffix = f"_{counter}"
        username = f"{base[: 50 - len(suffix)]}{suffix}"
        counter += 1
    return username


@transaction.atomic
def _sync_supabase_identity(identity, *, create_if_missing=False, profile=None):
    profile = profile or {}
    email = identity.email.strip().lower()
    user = User.objects.select_related("role").filter(email__iexact=email).first()

    if not user:
        if not create_if_missing and settings.SUPABASE_AUTH_REQUIRE_LOCAL_USER:
            raise LocalUserSyncError(
                "No local library account exists for this Supabase user."
            )
        role = _default_supabase_role()
        user = User(
            role=role,
            username=_username_from_email(email),
            email=email,
            full_name=profile.get("full_name") or email.split("@", 1)[0],
            phone=profile.get("phone", ""),
            address=profile.get("address", ""),
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        user.set_unusable_password()
        user.full_clean()
        user.save()
    else:
        changed_fields = []
        normalized_email = User.objects.normalize_email(email)
        if user.email != normalized_email:
            user.email = normalized_email
            changed_fields.append("email")
        for field in ("full_name", "phone", "address"):
            value = profile.get(field)
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)
        if changed_fields:
            try:
                user.full_clean()
                user.save(update_fields=changed_fields + ["updated_at"])
            except ValidationError as exc:
                raise LocalUserSyncError("; ".join(exc.messages)) from exc

    return _validate_local_login_user(user)


def _local_fallback_authenticate(request, *, identifier, password):
    user = User.objects.select_related("role").filter(email__iexact=identifier).first()
    if not user:
        user = User.objects.select_related("role").filter(username=identifier).first()
    if not user:
        return None
    _validate_local_login_user(user)
    authenticated = authenticate(
        request,
        username=user.username,
        password=password,
    )
    if authenticated:
        return _validate_local_login_user(
            User.objects.select_related("role").get(pk=authenticated.pk)
        )
    return None


def _login_local_user(request, user):
    user.backend = LOCAL_AUTH_BACKEND
    django_login(request, user)


def register_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = SupabaseAuthRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not settings.USE_SUPABASE_AUTH:
            form.add_error(
                None,
                "Supabase Auth is not enabled yet. Please configure Supabase first.",
            )
        else:
            try:
                identity = get_supabase_auth_service().sign_up(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    metadata={
                        "full_name": form.cleaned_data["full_name"],
                        "phone": form.cleaned_data.get("phone", ""),
                    },
                )
                user = _sync_supabase_identity(
                    identity,
                    create_if_missing=True,
                    profile={
                        "full_name": form.cleaned_data["full_name"],
                        "phone": form.cleaned_data.get("phone", ""),
                        "address": form.cleaned_data.get("address", ""),
                    },
                )
                if identity.has_session:
                    _store_supabase_session(request, identity)
                    _login_local_user(request, user)
                    messages.success(request, "Registration completed successfully.")
                    return redirect(settings.LOGIN_REDIRECT_URL)

                messages.success(
                    request,
                    "Registration created. Please confirm your email before login.",
                )
                return redirect("library:login")
            except (SupabaseAuthError, LocalUserSyncError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))

    return render(
        request,
        "library/register.html",
        {"form": form, "use_supabase_auth": settings.USE_SUPABASE_AUTH},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next_url(request))

    form = SupabaseAuthLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        try:
            if settings.USE_SUPABASE_AUTH:
                identity = get_supabase_auth_service().sign_in_with_password(
                    email=identifier,
                    password=password,
                )
                user = _sync_supabase_identity(identity)
                _store_supabase_session(request, identity)
            else:
                user = _local_fallback_authenticate(
                    request,
                    identifier=identifier,
                    password=password,
                )
                if not user:
                    raise LocalUserSyncError("Invalid email/username or password.")

            _login_local_user(request, user)
            audit_logger.info(
                "auth.library_login user_id=%s username=%s supabase=%s",
                user.pk,
                user.username,
                settings.USE_SUPABASE_AUTH,
            )
            return redirect(_safe_next_url(request))
        except (SupabaseAuthError, LocalUserSyncError) as exc:
            audit_logger.warning(
                "auth.library_login_failed identifier=%s supabase=%s",
                identifier,
                settings.USE_SUPABASE_AUTH,
            )
            form.add_error(None, getattr(exc, "message", str(exc)))

    return render(
        request,
        "library/login.html",
        {
            "form": form,
            "next": request.POST.get("next") or request.GET.get("next", ""),
            "use_supabase_auth": settings.USE_SUPABASE_AUTH,
        },
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        session = request.session.get(settings.SUPABASE_AUTH_SESSION_KEY, {})
        access_token = session.get("access_token")
        if settings.USE_SUPABASE_AUTH and access_token:
            try:
                get_supabase_auth_service().sign_out(access_token=access_token)
            except SupabaseAuthError as exc:
                error_logger.warning(
                    "auth.supabase_logout_failed user_id=%s error=%s",
                    request.user.pk,
                    exc.message,
                )
        _clear_supabase_session(request)
        django_logout(request)
        messages.success(request, "You have been logged out.")
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
def dashboard(request):
    _sync_overdue_records()

    recent_borrows = BorrowRecord.objects.select_related(
        "member__user", "book", "issued_by", "received_by"
    )
    if not is_library_staff(request.user):
        recent_borrows = recent_borrows.filter(member__user=request.user)

    context = {
        "total_books": Book.objects.count(),
        "total_members": Member.objects.count(),
        "available_books": Book.objects.filter(available_quantity__gt=0).count(),
        "borrowed_books": BorrowRecord.objects.filter(
            status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]
        ).count(),
        "overdue_books": BorrowRecord.objects.filter(
            status=BorrowRecord.OVERDUE
        ).count(),
        "unpaid_fines": Fine.objects.exclude(
            status__in=[Fine.PAID, Fine.WAIVED]
        ).count(),
        "recent_borrows": recent_borrows[:8],
        "can_manage": is_library_staff(request.user),
    }
    return render(request, "library/dashboard.html", context)


@staff_required
def entity_list(request, entity):
    config = _entity_config(entity)
    page_obj = _paginate(request, _entity_queryset(config))
    objects = page_obj.object_list
    rows = [{"pk": item.pk, "values": config["row"](item)} for item in objects]
    return render(
        request,
        "library/entity_list.html",
        {
            "entity": entity,
            "title": config["title"],
            "headers": config["headers"],
            "rows": rows,
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def entity_create(request, entity):
    config = _entity_config(entity)
    form_class = config.get("create_form", config.get("form"))
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config['title'][:-1]} created successfully.")
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": f"Add {config['title'][:-1]}", "entity": entity},
    )


@staff_required
def entity_update(request, entity, pk):
    config = _entity_config(entity)
    instance = get_object_or_404(config["model"], pk=pk)
    form_class = config.get("update_form", config.get("form"))
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config['title'][:-1]} updated successfully.")
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/entity_form.html",
        {
            "form": form,
            "title": f"Edit {config['title'][:-1]}",
            "entity": entity,
        },
    )


@staff_required
def entity_delete(request, entity, pk):
    config = _entity_config(entity)
    instance = get_object_or_404(config["model"], pk=pk)
    if request.method == "POST":
        try:
            instance.delete()
            messages.success(request, f"{config['title'][:-1]} deleted successfully.")
        except ProtectedError:
            error_logger.warning(
                "delete.protected entity=%s pk=%s user_id=%s",
                entity,
                pk,
                request.user.pk,
            )
            messages.error(
                request,
                (
                    "This record is referenced by other library data and "
                    "cannot be deleted."
                ),
            )
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/confirm_delete.html",
        {"object": instance, "title": f"Delete {config['title'][:-1]}"},
    )


@login_required
def book_list(request):
    books = Book.objects.select_related("author", "publisher", "category")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(isbn__icontains=query)
            | Q(author__author_name__icontains=query)
            | Q(publisher__publisher_name__icontains=query)
            | Q(category__category_name__icontains=query)
            | Q(shelf_location__icontains=query)
        )
    if status:
        books = books.filter(status=status)
    if category and category.isdigit():
        books = books.filter(category_id=category)
    page_obj = _paginate(request, books)

    return render(
        request,
        "library/book_list.html",
        {
            "books": page_obj,
            "categories": Category.objects.all(),
            "status_choices": Book.STATUS_CHOICES,
            "query": query,
            "selected_status": status,
            "selected_category": category,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def book_create(request):
    form = BookForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Book created successfully.")
        return redirect("library:book_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Add Book", "cancel_url": "library:book_list"},
    )


@staff_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Book updated successfully.")
        return redirect("library:book_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Edit Book", "cancel_url": "library:book_list"},
    )


@staff_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        try:
            book.delete()
            messages.success(request, "Book deleted successfully.")
        except ProtectedError:
            error_logger.warning(
                "book.delete_protected book_id=%s user_id=%s", pk, request.user.pk
            )
            messages.error(request, "A book with borrowing history cannot be deleted.")
        return redirect("library:book_list")
    return render(
        request,
        "library/confirm_delete.html",
        {"object": book, "title": "Delete Book", "cancel_url": "library:book_list"},
    )


@login_required
def borrow_list(request):
    _sync_overdue_records()
    records = BorrowRecord.objects.select_related(
        "member__user", "book", "issued_by", "received_by"
    )
    if not is_library_staff(request.user):
        records = records.filter(member__user=request.user)
    status = request.GET.get("status", "").strip()
    if status:
        records = records.filter(status=status)
    page_obj = _paginate(request, records)
    return render(
        request,
        "library/borrow_list.html",
        {
            "records": page_obj,
            "status_choices": BorrowRecord.STATUS_CHOICES,
            "selected_status": status,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
@transaction.atomic
def borrow_create(request):
    form = BorrowForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        book = Book.objects.select_for_update().get(pk=form.cleaned_data["book"].pk)
        if book.available_quantity < 1 or book.status != Book.AVAILABLE:
            form.add_error("book", "This book is no longer available.")
        else:
            borrow_record = form.save(commit=False)
            borrow_record.book = book
            borrow_record.issued_by = request.user
            borrow_record.status = BorrowRecord.BORROWED
            borrow_record.save()

            book.available_quantity -= 1
            book.status = (
                Book.BORROWED if book.available_quantity == 0 else Book.AVAILABLE
            )
            book.save(update_fields=["available_quantity", "status", "updated_at"])
            audit_logger.info(
                "borrow.issue borrow_id=%s member_id=%s book_id=%s issued_by=%s",
                borrow_record.pk,
                borrow_record.member_id,
                borrow_record.book_id,
                request.user.pk,
            )

            messages.success(request, "Book issued successfully.")
            return redirect("library:borrow_list")
    return render(request, "library/borrow_form.html", {"form": form})


@staff_required
@transaction.atomic
def borrow_return(request, pk):
    borrow_record = get_object_or_404(
        BorrowRecord.objects.select_for_update().select_related("book", "member__user"),
        pk=pk,
    )
    if borrow_record.status not in {BorrowRecord.BORROWED, BorrowRecord.OVERDUE}:
        messages.error(request, "Only active borrow records can be returned.")
        return redirect("library:borrow_list")

    form = ReturnForm(request.POST or None, borrow_record=borrow_record)
    if request.method == "POST" and form.is_valid():
        return_date = form.cleaned_data["return_date"]
        borrow_record.return_date = return_date
        borrow_record.received_by = request.user
        borrow_record.status = BorrowRecord.RETURNED
        borrow_record.save()

        book = Book.objects.select_for_update().get(pk=borrow_record.book_id)
        book.available_quantity = min(book.quantity, book.available_quantity + 1)
        book.status = Book.AVAILABLE
        book.save(update_fields=["available_quantity", "status", "updated_at"])

        days_overdue = max((return_date - borrow_record.due_date).days, 0)
        if days_overdue:
            amount = FINE_RATE_PER_DAY * days_overdue
            fine = Fine.objects.filter(
                borrow=borrow_record, member=borrow_record.member
            ).first()
            if fine:
                fine.amount = amount
                if fine.paid_amount > amount:
                    fine.paid_amount = amount
                fine.status = Fine.PAID if fine.paid_amount == amount else Fine.UNPAID
                fine.paid_date = timezone.now() if fine.status == Fine.PAID else None
                fine.save()
            else:
                Fine.objects.create(
                    borrow=borrow_record,
                    member=borrow_record.member,
                    amount=amount,
                )
            Notification.objects.create(
                member=borrow_record.member,
                title="Overdue fine created",
                message=(
                    f"A fine of {amount} was created for returning "
                    f"{borrow_record.book.title} {days_overdue} day(s) late."
                ),
                notification_type=Notification.FINE,
            )

        audit_logger.info(
            (
                "borrow.return borrow_id=%s member_id=%s book_id=%s "
                "received_by=%s days_overdue=%s"
            ),
            borrow_record.pk,
            borrow_record.member_id,
            borrow_record.book_id,
            request.user.pk,
            days_overdue,
        )

        messages.success(request, "Book returned successfully.")
        return redirect("library:borrow_list")
    return render(
        request,
        "library/return_form.html",
        {"form": form, "borrow_record": borrow_record},
    )


@login_required
def fine_list(request):
    fines = Fine.objects.select_related("borrow__book", "member__user")
    if not is_library_staff(request.user):
        fines = fines.filter(member__user=request.user)
    page_obj = _paginate(request, fines)
    return render(
        request,
        "library/fine_list.html",
        {
            "fines": page_obj,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def fine_create(request):
    form = FineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fine saved successfully.")
        return redirect("library:fine_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Add Fine", "cancel_url": "library:fine_list"},
    )


@staff_required
@transaction.atomic
def fine_pay(request, pk):
    fine = get_object_or_404(
        Fine.objects.select_for_update().select_related("member__user", "borrow__book"),
        pk=pk,
    )
    if fine.status in {Fine.PAID, Fine.WAIVED}:
        messages.info(request, "This fine has no payable balance.")
        return redirect("library:fine_list")

    form = FinePaymentForm(request.POST or None, fine=fine)
    if request.method == "POST" and form.is_valid():
        fine.paid_amount += form.cleaned_data["payment_amount"]
        if fine.paid_amount == fine.amount:
            fine.status = Fine.PAID
            fine.paid_date = timezone.now()
        else:
            fine.status = Fine.PARTIALLY_PAID
            fine.paid_date = None
        fine.save()
        audit_logger.info(
            "fine.payment fine_id=%s member_id=%s amount=%s user_id=%s",
            fine.pk,
            fine.member_id,
            form.cleaned_data["payment_amount"],
            request.user.pk,
        )
        messages.success(request, "Fine payment recorded successfully.")
        return redirect("library:fine_list")
    return render(
        request,
        "library/fine_payment_form.html",
        {"form": form, "fine": fine},
    )


@login_required
def notification_list(request):
    notifications = Notification.objects.select_related("member__user")
    if not is_library_staff(request.user):
        notifications = notifications.filter(member__user=request.user)
    page_obj = _paginate(request, notifications)
    return render(
        request,
        "library/notification_list.html",
        {
            "notifications": page_obj,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def notification_create(request):
    form = NotificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Member notification created successfully.")
        return redirect("library:notification_list")
    return render(
        request,
        "library/entity_form.html",
        {
            "form": form,
            "title": "Add Notification",
            "cancel_url": "library:notification_list",
        },
    )


@login_required
def notification_read(request, pk):
    notification = get_object_or_404(
        Notification.objects.select_related("member__user"), pk=pk
    )
    if not is_library_staff(request.user):
        get_object_or_404(Member, pk=notification.member_id, user=request.user)
    if request.method == "POST":
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect("library:notification_list")


def _report_rows(report_type):
    if report_type == Report.BOOKS:
        yield ["Book ID", "Title", "ISBN", "Author", "Available", "Status"]
        for book in Book.objects.select_related("author"):
            yield [
                book.book_id,
                book.title,
                book.isbn,
                book.author.author_name,
                book.available_quantity,
                book.status,
            ]
    elif report_type == Report.MEMBERS:
        yield ["Member ID", "Code", "Name", "Type", "Department", "Status"]
        for member in Member.objects.select_related("user"):
            yield [
                member.member_id,
                member.member_code,
                member.user.full_name,
                member.member_type,
                member.department,
                member.status,
            ]
    elif report_type == Report.BORROWING:
        yield ["Borrow ID", "Member", "Book", "Borrowed", "Due", "Returned", "Status"]
        for record in BorrowRecord.objects.select_related("member", "book"):
            yield [
                record.borrow_id,
                record.member.member_code,
                record.book.title,
                record.borrow_date,
                record.due_date,
                record.return_date or "",
                record.status,
            ]
    else:
        yield ["Fine ID", "Member", "Book", "Amount", "Paid", "Balance", "Status"]
        for fine in Fine.objects.select_related("member", "borrow__book"):
            yield [
                fine.fine_id,
                fine.member.member_code,
                fine.borrow.book.title,
                fine.amount,
                fine.paid_amount,
                fine.balance,
                fine.status,
            ]


def _create_report_file(report):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(_report_rows(report.report_type))
    filename = (
        f"{report.report_type}_report_"
        f"{timezone.localtime(report.generated_at):%Y%m%d_%H%M%S}.csv"
    )
    report.file_path.save(
        filename,
        ContentFile(output.getvalue().encode("utf-8")),
        save=True,
    )


@staff_required
def report_list(request):
    reports = Report.objects.select_related("generated_by")
    borrowing_summary = (
        Book.objects.annotate(borrow_count=Count("borrow_records"))
        .filter(borrow_count__gt=0)
        .order_by("-borrow_count", "title")[:5]
    )
    page_obj = _paginate(request, reports)
    return render(
        request,
        "library/report_list.html",
        {
            "reports": page_obj,
            "borrowing_summary": borrowing_summary,
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def report_create(request):
    form = ReportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.generated_by = request.user
        report.save()
        if not report.file_path:
            _create_report_file(report)
        audit_logger.info(
            "report.generate report_id=%s report_type=%s generated_by=%s",
            report.pk,
            report.report_type,
            request.user.pk,
        )
        messages.success(request, "Report generated successfully.")
        return redirect("library:report_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Generate Report", "cancel_url": "library:report_list"},
    )

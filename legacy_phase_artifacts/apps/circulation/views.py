from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin
from apps.catalog.models import Book

from .forms import (
    BorrowBookForm,
    BorrowingPolicyForm,
    RenewalForm,
    ReservationForm,
    ReservationStatusForm,
    ReturnBookForm,
)
from .models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord
from .services import (
    borrow_book,
    mark_expired_reservations,
    mark_overdue_records,
    renew_borrow,
    reserve_book,
    return_book,
    update_reservation_status,
)


class BorrowRecordListView(RolePermissionRequiredMixin, ListView):
    model = BorrowRecord
    template_name = "circulation/borrow_list.html"
    context_object_name = "borrow_records"
    paginate_by = 20
    permission_codename = "circulation.view_borrow"

    def get_queryset(self):
        mark_overdue_records()
        queryset = BorrowRecord.objects.select_related(
            "member__user", "book_copy__book", "borrowed_by"
        ).visible_to(self.request.user)
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(member__member_code__icontains=term)
                | Q(member__user__username__icontains=term)
                | Q(member__user__first_name__icontains=term)
                | Q(member__user__last_name__icontains=term)
                | Q(book_copy__copy_code__icontains=term)
                | Q(book_copy__barcode__icontains=term)
                | Q(book_copy__book__title__icontains=term)
                | Q(book_copy__book__isbn__icontains=term)
                | Q(book_copy__book__book_code__icontains=term)
            )
        if status in dict(BorrowRecord.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset.order_by("-borrow_date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = BorrowRecord.objects.visible_to(self.request.user)
        context["statuses"] = BorrowRecord.STATUS_CHOICES
        context["summary"] = {
            "active": visible.active().count(),
            "overdue": visible.filter(status=BorrowRecord.OVERDUE).count(),
            "returned": visible.filter(status=BorrowRecord.RETURNED).count(),
            "total": visible.count(),
        }
        return context


class BorrowRecordDetailView(RolePermissionRequiredMixin, DetailView):
    model = BorrowRecord
    template_name = "circulation/borrow_detail.html"
    context_object_name = "borrow_record"
    permission_codename = "circulation.view_borrow"

    def get_queryset(self):
        return (
            BorrowRecord.objects.select_related(
                "member__user", "book_copy__book", "borrowed_by"
            )
            .prefetch_related("renewals", "fines")
            .visible_to(self.request.user)
        )

    def get_object(self, queryset=None):
        record = super().get_object(queryset)
        record.refresh_overdue_status()
        return record


class BorrowBookView(RolePermissionRequiredMixin, FormView):
    template_name = "circulation/borrow_form.html"
    form_class = BorrowBookForm
    permission_codename = "circulation.create_borrow"

    def form_valid(self, form):
        try:
            record = borrow_book(
                member=form.cleaned_data["member"],
                book_copy=form.cleaned_data["book_copy"],
                borrowed_by=self.request.user,
                borrow_date=form.cleaned_data["borrow_date"],
                due_date=form.cleaned_data["due_date"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Book issued successfully.")
        return redirect("circulation:borrow_detail", pk=record.pk)


class ReturnBookView(RolePermissionRequiredMixin, FormView):
    template_name = "circulation/return_form.html"
    form_class = ReturnBookForm
    permission_codename = "circulation.return_book"

    def get_borrow_record(self):
        pk = self.kwargs.get("pk")
        if not pk:
            return None
        return get_object_or_404(
            BorrowRecord.objects.active().select_related(
                "member__user", "book_copy__book"
            ),
            pk=pk,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["borrow_record"] = self.get_borrow_record()
        return kwargs

    def form_valid(self, form):
        try:
            return_record = return_book(
                borrow_record=form.cleaned_data["borrow_record"],
                returned_by=self.request.user,
                return_date=form.cleaned_data["return_date"],
                book_condition=form.cleaned_data["book_condition"],
                remarks=form.cleaned_data["remarks"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        if return_record.fine_amount:
            messages.warning(
                self.request,
                f"Book returned with a late fine of {return_record.fine_amount}.",
            )
        else:
            messages.success(self.request, "Book returned successfully.")
        return redirect("circulation:borrow_detail", pk=return_record.borrow_record.pk)


class RenewBorrowView(RolePermissionRequiredMixin, FormView):
    template_name = "circulation/renew_form.html"
    form_class = RenewalForm
    permission_codename = "circulation.renew_borrow"

    def dispatch(self, request, *args, **kwargs):
        self.borrow_record = get_object_or_404(
            BorrowRecord.objects.select_related(
                "member__user", "book_copy__book"
            ).visible_to(request.user),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["borrow_record"] = self.borrow_record
        return context

    def form_valid(self, form):
        try:
            renewal = renew_borrow(
                borrow_record=self.borrow_record,
                renewed_by=self.request.user,
                remarks=form.cleaned_data["remarks"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Borrow record renewed until {renewal.new_due_date}.",
        )
        return redirect("circulation:borrow_detail", pk=self.borrow_record.pk)


class RenewalListView(RolePermissionRequiredMixin, ListView):
    model = RenewalRecord
    template_name = "circulation/renewal_list.html"
    context_object_name = "renewals"
    paginate_by = 20
    permission_codename = "circulation.view_borrow"

    def get_queryset(self):
        queryset = RenewalRecord.objects.select_related(
            "borrow_record__member__user",
            "borrow_record__book_copy__book",
            "renewed_by",
        )
        if not (
            self.request.user.is_superuser
            or self.request.user.has_role(
                "super_admin", "admin", "librarian", "assistant_librarian"
            )
        ):
            queryset = queryset.filter(borrow_record__member__user=self.request.user)
        return queryset


class ReturnRecordListView(RolePermissionRequiredMixin, ListView):
    model = ReturnRecord
    template_name = "circulation/return_list.html"
    context_object_name = "returns"
    paginate_by = 20
    permission_codename = "circulation.view_borrow"

    def get_queryset(self):
        queryset = ReturnRecord.objects.select_related(
            "borrow_record__member__user",
            "borrow_record__book_copy__book",
            "returned_by",
        )
        if not (
            self.request.user.is_superuser
            or self.request.user.has_role(
                "super_admin", "admin", "librarian", "assistant_librarian"
            )
        ):
            queryset = queryset.filter(borrow_record__member__user=self.request.user)
        return queryset


class ReservationListView(RolePermissionRequiredMixin, ListView):
    model = Reservation
    template_name = "circulation/reservation_list.html"
    context_object_name = "reservations"
    paginate_by = 20
    permission_codename = "circulation.manage_reservation"

    def get_queryset(self):
        mark_expired_reservations()
        queryset = Reservation.objects.select_related("member__user", "book").visible_to(
            self.request.user
        )
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(member__member_code__icontains=term)
                | Q(member__user__username__icontains=term)
                | Q(member__user__first_name__icontains=term)
                | Q(member__user__last_name__icontains=term)
                | Q(book__title__icontains=term)
                | Q(book__book_code__icontains=term)
            )
        if status in dict(Reservation.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset.order_by("status", "reserved_date", "created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = Reservation.objects.visible_to(self.request.user)
        context["statuses"] = Reservation.STATUS_CHOICES
        context["summary"] = {
            "pending": visible.filter(status=Reservation.PENDING).count(),
            "ready": visible.filter(status=Reservation.READY).count(),
            "fulfilled": visible.filter(status=Reservation.FULFILLED).count(),
            "cancelled": visible.filter(status=Reservation.CANCELLED).count(),
        }
        return context


class ReservationCreateView(RolePermissionRequiredMixin, FormView):
    template_name = "circulation/reservation_form.html"
    form_class = ReservationForm
    permission_codename = "circulation.manage_reservation"

    def dispatch(self, request, *args, **kwargs):
        self.book = None
        book_id = request.GET.get("book") or request.POST.get("book_context")
        if book_id and str(book_id).isdigit():
            self.book = get_object_or_404(Book, pk=book_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        kwargs["book"] = self.book
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_book"] = self.book
        return context

    def form_valid(self, form):
        try:
            reserve_book(
                member=form.cleaned_data["member"],
                book=form.cleaned_data["book"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Reservation created successfully.")
        return redirect("circulation:reservation_list")


class ReservationUpdateView(RolePermissionRequiredMixin, FormView):
    form_class = ReservationStatusForm
    template_name = "circulation/reservation_status_form.html"
    permission_codename = "circulation.manage_reservation"

    def dispatch(self, request, *args, **kwargs):
        self.reservation = get_object_or_404(
            Reservation.objects.select_related("member__user", "book").visible_to(
                request.user
            ),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        kwargs["reservation"] = self.reservation
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reservation"] = self.reservation
        return context

    def form_valid(self, form):
        try:
            reservation = update_reservation_status(
                self.reservation,
                form.cleaned_data["status"],
                changed_by=self.request.user,
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Reservation updated to {reservation.get_status_display()}.",
        )
        return redirect("circulation:reservation_list")


class BorrowingPolicyListView(RolePermissionRequiredMixin, ListView):
    model = BorrowingPolicy
    template_name = "circulation/policy_list.html"
    context_object_name = "policies"
    permission_codename = "circulation.manage_policy"


class BorrowingPolicyUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = BorrowingPolicy
    form_class = BorrowingPolicyForm
    template_name = "circulation/policy_form.html"
    success_url = reverse_lazy("circulation:policy_list")
    permission_codename = "circulation.manage_policy"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Borrowing policy updated successfully.")
        return response

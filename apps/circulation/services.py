from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Book, BookCopy
from apps.members.models import Member

from .models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord


DEFAULT_POLICIES = {
    "student": {"max_books": 3, "loan_period_days": 14, "renewal_days": 7, "max_renewals": 1, "fine_per_day": Decimal("1.00"), "reservation_expiry_days": 2},
    "teacher": {"max_books": 8, "loan_period_days": 30, "renewal_days": 14, "max_renewals": 2, "fine_per_day": Decimal("1.00"), "reservation_expiry_days": 3},
    "staff": {"max_books": 5, "loan_period_days": 21, "renewal_days": 7, "max_renewals": 1, "fine_per_day": Decimal("1.00"), "reservation_expiry_days": 2},
    "librarian": {"max_books": 6, "loan_period_days": 21, "renewal_days": 7, "max_renewals": 2, "fine_per_day": Decimal("1.00"), "reservation_expiry_days": 2},
    "assistant_librarian": {"max_books": 4, "loan_period_days": 14, "renewal_days": 7, "max_renewals": 1, "fine_per_day": Decimal("1.00"), "reservation_expiry_days": 2},
}


def get_policy(member, lock=False):
    defaults = DEFAULT_POLICIES.get(member.member_type, DEFAULT_POLICIES["student"])
    queryset = BorrowingPolicy.objects
    if lock:
        queryset = queryset.select_for_update()
    policy = queryset.filter(member_type=member.member_type).first()
    if not policy:
        policy = BorrowingPolicy.objects.create(member_type=member.member_type, **defaults)
    return policy


def sync_book_status(book):
    copy_statuses = set(book.copies.values_list("status", flat=True))
    if BookCopy.AVAILABLE in copy_statuses or not copy_statuses:
        status = Book.AVAILABLE
    elif BookCopy.BORROWED in copy_statuses:
        status = Book.BORROWED
    elif BookCopy.UNDER_REPAIR in copy_statuses:
        status = Book.UNDER_REPAIR
    elif BookCopy.DAMAGED in copy_statuses:
        status = Book.DAMAGED
    else:
        status = Book.LOST
    Book.objects.filter(pk=book.pk).exclude(status=status).update(status=status)
    book.status = status


def _log_copy_status_change(book_copy, previous_status, new_status, reason, changed_by=None, notes=""):
    try:
        from apps.status_tracking.services import log_status_change
    except ImportError:
        return
    log_status_change(
        book_copy=book_copy,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        changed_by=changed_by,
        notes=notes,
    )


def active_borrow_count(member):
    return BorrowRecord.objects.active().filter(member=member).count()


def member_has_unpaid_fines(member):
    from apps.fines.models import Fine

    return Fine.objects.filter(member=member).exclude(
        status__in=[Fine.PAID, Fine.WAIVED]
    ).exists()


def validate_member_account(member):
    if not member.is_membership_valid:
        raise ValidationError("Only active, unexpired members can use circulation services.")


def validate_member_can_borrow(member, policy=None):
    validate_member_account(member)
    if member_has_unpaid_fines(member):
        raise ValidationError("This member has unpaid fines and cannot borrow new books.")
    policy = policy or get_policy(member)
    if not policy.is_active:
        raise ValidationError("Borrowing is currently disabled for this member type.")
    if active_borrow_count(member) >= policy.max_books:
        raise ValidationError(
            f"Borrowing limit reached. Maximum allowed books: {policy.max_books}."
        )
    return policy


@transaction.atomic
def borrow_book(
    member,
    book_copy,
    borrowed_by,
    borrow_date=None,
    due_date=None,
    notes="",
    allow_due_date_override=False,
):
    member = (
        Member.objects.select_for_update()
        .select_related("user", "user__role")
        .get(pk=member.pk)
    )
    book_copy = (
        BookCopy.objects.select_for_update()
        .select_related("book")
        .get(pk=book_copy.pk)
    )
    policy = get_policy(member, lock=True)
    validate_member_can_borrow(member, policy)

    borrow_date = borrow_date or timezone.localdate()
    if borrow_date > timezone.localdate():
        raise ValidationError("Borrow date cannot be in the future.")
    if book_copy.status != BookCopy.AVAILABLE:
        raise ValidationError("This book copy is not available for borrowing.")
    if BorrowRecord.objects.active().filter(book_copy=book_copy).exists():
        raise ValidationError("This book copy already has an active borrow record.")
    if BorrowRecord.objects.active().filter(
        member=member,
        book_copy__book=book_copy.book,
    ).exists():
        raise ValidationError("This member already has an active loan for this title.")

    Reservation.objects.select_for_update().filter(
        book=book_copy.book,
        status=Reservation.READY,
        expiry_date__lt=timezone.localdate(),
    ).update(status=Reservation.EXPIRED, updated_at=timezone.now())
    ready_reservation = (
        Reservation.objects.select_for_update()
        .filter(book=book_copy.book, status=Reservation.READY)
        .order_by("ready_date", "created_at")
        .first()
    )
    if not ready_reservation:
        pending_reservation = (
            Reservation.objects.select_for_update()
            .filter(book=book_copy.book, status=Reservation.PENDING)
            .order_by("reserved_date", "created_at")
            .first()
        )
        if pending_reservation and pending_reservation.member_id != member.pk:
            raise ValidationError("This title is reserved for another member.")
    elif ready_reservation.member_id != member.pk:
        raise ValidationError("This copy is held for another member's reservation.")

    maximum_due_date = borrow_date + timedelta(days=policy.loan_period_days)
    due_date = due_date or maximum_due_date
    if due_date < borrow_date:
        raise ValidationError("Due date cannot be earlier than borrow date.")
    if due_date > maximum_due_date and not allow_due_date_override:
        raise ValidationError(
            f"Due date exceeds the {policy.loan_period_days}-day policy limit."
        )

    borrow_record = BorrowRecord.objects.create(
        member=member,
        book_copy=book_copy,
        borrowed_by=borrowed_by,
        borrow_date=borrow_date,
        due_date=due_date,
        fine_rate_per_day=policy.fine_per_day,
        notes=notes,
    )
    previous_status = book_copy.status
    book_copy.status = BookCopy.BORROWED
    book_copy.save(update_fields=["status", "updated_at"])
    sync_book_status(book_copy.book)
    _log_copy_status_change(
        book_copy,
        previous_status,
        BookCopy.BORROWED,
        "Book borrowed",
        changed_by=borrowed_by,
    )

    Reservation.objects.filter(
        member=member,
        book=book_copy.book,
        status__in=[Reservation.PENDING, Reservation.READY],
    ).update(status=Reservation.FULFILLED, updated_at=timezone.now())
    return borrow_record


@transaction.atomic
def return_book(
    borrow_record,
    returned_by,
    return_date=None,
    book_condition=ReturnRecord.GOOD,
    remarks="",
):
    from apps.fines.models import Fine

    borrow_record = (
        BorrowRecord.objects.select_for_update()
        .select_related("member__user", "book_copy__book")
        .get(pk=borrow_record.pk)
    )
    book_copy = (
        BookCopy.objects.select_for_update()
        .select_related("book")
        .get(pk=borrow_record.book_copy_id)
    )
    return_date = return_date or timezone.localdate()
    if return_date > timezone.localdate():
        raise ValidationError("Return date cannot be in the future.")
    if not borrow_record.is_active:
        raise ValidationError("Only active borrow records can be returned.")
    if ReturnRecord.objects.filter(borrow_record=borrow_record).exists():
        raise ValidationError("This borrow record already has a return record.")
    if return_date < borrow_record.borrow_date:
        raise ValidationError("Return date cannot be earlier than borrow date.")

    days_late = max((return_date - borrow_record.due_date).days, 0)
    fine_amount = borrow_record.fine_rate_per_day * days_late
    return_record = ReturnRecord.objects.create(
        borrow_record=borrow_record,
        returned_by=returned_by,
        return_date=return_date,
        book_condition=book_condition,
        fine_amount=fine_amount,
        remarks=remarks,
    )

    borrow_record.return_date = return_date
    if book_condition == ReturnRecord.LOST:
        borrow_record.status = BorrowRecord.LOST
        copy_status = BookCopy.LOST
    elif book_condition == ReturnRecord.DAMAGED:
        borrow_record.status = BorrowRecord.DAMAGED
        copy_status = BookCopy.DAMAGED
    elif book_condition == ReturnRecord.UNDER_REPAIR:
        borrow_record.status = BorrowRecord.DAMAGED
        copy_status = BookCopy.UNDER_REPAIR
    else:
        borrow_record.status = BorrowRecord.RETURNED
        copy_status = BookCopy.AVAILABLE
    borrow_record.save(update_fields=["return_date", "status", "updated_at"])

    previous_status = book_copy.status
    book_copy.status = copy_status
    update_fields = ["status", "updated_at"]
    if copy_status in {BookCopy.DAMAGED, BookCopy.UNDER_REPAIR}:
        book_copy.condition = BookCopy.DAMAGED_CONDITION
        update_fields.append("condition")
    book_copy.save(update_fields=update_fields)
    sync_book_status(book_copy.book)
    _log_copy_status_change(
        book_copy,
        previous_status,
        copy_status,
        f"Book returned as {book_condition}",
        changed_by=returned_by,
        notes=remarks,
    )
    _create_return_condition_records(
        book_copy,
        borrow_record,
        returned_by,
        book_condition,
        remarks,
    )

    if fine_amount > Decimal("0.00"):
        Fine.objects.get_or_create(
            borrow_record=borrow_record,
            reason=Fine.LATE_RETURN,
            defaults={
                "member": borrow_record.member,
                "amount": fine_amount,
                "description": f"Late return by {days_late} day(s).",
                "created_by": returned_by,
            },
        )

    if copy_status == BookCopy.AVAILABLE:
        promote_next_reservation(book_copy.book)
    return return_record


def _create_return_condition_records(
    book_copy,
    borrow_record,
    returned_by,
    book_condition,
    remarks,
):
    if book_condition == ReturnRecord.GOOD:
        return
    try:
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        from apps.status_tracking.models import DamagedBook, LostBook, RepairRecord
    except ImportError:
        return

    if book_condition == ReturnRecord.LOST:
        LostBook.objects.get_or_create(
            book_copy=book_copy,
            borrow_record=borrow_record,
            defaults={
                "member": borrow_record.member,
                "reported_by": returned_by,
                "description": remarks,
            },
        )
        create_notification(
            recipient=borrow_record.member,
            title="Lost book recorded",
            message=f"'{book_copy.book.title}' ({book_copy.copy_code}) has been recorded as lost.",
            notification_type=Notification.LOST_BOOK,
            channel=Notification.IN_APP,
            priority=Notification.HIGH,
            related_borrow_record=borrow_record,
            related_book_copy=book_copy,
            created_by=returned_by,
        )
        return

    damaged_record, _ = DamagedBook.objects.get_or_create(
        book_copy=book_copy,
        borrow_record=borrow_record,
        defaults={
            "member": borrow_record.member,
            "reported_by": returned_by,
            "severity": DamagedBook.MODERATE,
            "description": remarks,
            "status": (
                DamagedBook.SENT_REPAIR
                if book_condition == ReturnRecord.UNDER_REPAIR
                else DamagedBook.REPORTED
            ),
        },
    )
    create_notification(
        recipient=borrow_record.member,
        title="Damaged book recorded",
        message=f"'{book_copy.book.title}' ({book_copy.copy_code}) has been recorded as damaged.",
        notification_type=Notification.DAMAGED_BOOK,
        channel=Notification.IN_APP,
        priority=Notification.NORMAL,
        related_borrow_record=borrow_record,
        related_book_copy=book_copy,
        created_by=returned_by,
    )
    if book_condition == ReturnRecord.UNDER_REPAIR:
        RepairRecord.objects.get_or_create(
            book_copy=book_copy,
            damage_record=damaged_record,
            defaults={"sent_by": returned_by, "notes": remarks},
        )


@transaction.atomic
def renew_borrow(borrow_record, renewed_by, remarks=""):
    borrow_record = (
        BorrowRecord.objects.select_for_update()
        .select_related("member__user", "member__user__role", "book_copy__book")
        .get(pk=borrow_record.pk)
    )
    if not borrow_record.is_active:
        raise ValidationError("Only active borrow records can be renewed.")
    if timezone.localdate() > borrow_record.due_date:
        raise ValidationError("Overdue books must be returned before they can be renewed.")
    validate_member_account(borrow_record.member)
    if member_has_unpaid_fines(borrow_record.member):
        raise ValidationError("Outstanding fines must be paid before renewal.")
    policy = get_policy(borrow_record.member, lock=True)
    if not policy.is_active:
        raise ValidationError("Renewals are disabled for this member type.")
    if borrow_record.renewal_count >= policy.max_renewals:
        raise ValidationError(
            f"Renewal limit reached. Maximum renewals: {policy.max_renewals}."
        )
    if Reservation.objects.active().filter(book=borrow_record.book_copy.book).exclude(
        member=borrow_record.member
    ).exists():
        raise ValidationError("This book cannot be renewed because another member reserved it.")

    old_due_date = borrow_record.due_date
    new_due_date = old_due_date + timedelta(days=policy.renewal_days)
    borrow_record.due_date = new_due_date
    borrow_record.renewal_count += 1
    borrow_record.save(update_fields=["due_date", "renewal_count", "updated_at"])
    return RenewalRecord.objects.create(
        borrow_record=borrow_record,
        renewed_by=renewed_by,
        old_due_date=old_due_date,
        new_due_date=new_due_date,
        remarks=remarks,
    )


@transaction.atomic
def reserve_book(member, book, expiry_date=None, notes=""):
    member = (
        Member.objects.select_for_update()
        .select_related("user", "user__role")
        .get(pk=member.pk)
    )
    book = Book.objects.select_for_update().get(pk=book.pk)
    validate_member_account(member)
    policy = get_policy(member, lock=True)
    if not policy.is_active:
        raise ValidationError("Reservations are disabled for this member type.")
    if member_has_unpaid_fines(member):
        raise ValidationError("Outstanding fines must be paid before making a reservation.")
    if not book.copies.exists():
        raise ValidationError("This title has no registered copies and cannot be reserved.")
    if book.copies.filter(status=BookCopy.AVAILABLE).exists():
        raise ValidationError("This book has an available copy and does not need a reservation.")
    if BorrowRecord.objects.active().filter(
        member=member,
        book_copy__book=book,
    ).exists():
        raise ValidationError("This member already has an active loan for this title.")
    if Reservation.objects.active().filter(member=member, book=book).exists():
        raise ValidationError("This member already has an active reservation for this book.")

    return Reservation.objects.create(
        member=member,
        book=book,
        expiry_date=None,
        notes=notes,
    )


def _notify_reservation_ready(reservation):
    try:
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
    except ImportError:
        return
    create_notification(
        recipient=reservation.member,
        title="Reserved book ready for pickup",
        message=(
            f"'{reservation.book.title}' is ready for pickup until "
            f"{reservation.expiry_date:%Y-%m-%d}."
        ),
        notification_type=Notification.RESERVATION,
        channel=Notification.IN_APP,
        priority=Notification.HIGH,
    )


@transaction.atomic
def promote_next_reservation(book):
    book = Book.objects.select_for_update().get(pk=book.pk)
    if not book.copies.filter(status=BookCopy.AVAILABLE).exists():
        return None
    existing_ready = (
        Reservation.objects.select_for_update()
        .filter(book=book, status=Reservation.READY)
        .order_by("ready_date", "created_at")
        .first()
    )
    if existing_ready:
        return existing_ready
    reservation = (
        Reservation.objects.select_for_update()
        .filter(book=book, status=Reservation.PENDING)
        .order_by("reserved_date", "created_at")
        .first()
    )
    if reservation:
        policy = get_policy(reservation.member, lock=True)
        reservation.status = Reservation.READY
        reservation.ready_date = timezone.localdate()
        reservation.expiry_date = reservation.ready_date + timedelta(
            days=policy.reservation_expiry_days
        )
        reservation.save(
            update_fields=["status", "ready_date", "expiry_date", "updated_at"]
        )
        _notify_reservation_ready(reservation)
    return reservation


@transaction.atomic
def update_reservation_status(reservation, status, changed_by=None, notes=""):
    reservation = (
        Reservation.objects.select_for_update()
        .select_related("member__user", "book")
        .get(pk=reservation.pk)
    )
    if not reservation.is_active:
        raise ValidationError("Completed reservations cannot be changed.")
    if status == Reservation.CANCELLED:
        reservation.status = status
        if notes:
            reservation.notes = notes
        reservation.save(update_fields=["status", "notes", "updated_at"])
        if reservation.book.copies.filter(status=BookCopy.AVAILABLE).exists():
            promote_next_reservation(reservation.book)
        return reservation
    if status == Reservation.READY:
        if reservation.status != Reservation.PENDING:
            raise ValidationError("Only pending reservations can be marked ready.")
        if not reservation.book.copies.filter(status=BookCopy.AVAILABLE).exists():
            raise ValidationError("No copy is available to mark this reservation ready.")
        other_ready = Reservation.objects.filter(
            book=reservation.book,
            status=Reservation.READY,
        ).exclude(pk=reservation.pk)
        if other_ready.exists():
            raise ValidationError("Another reservation is already ready for this title.")
        policy = get_policy(reservation.member, lock=True)
        reservation.status = status
        reservation.ready_date = timezone.localdate()
        reservation.expiry_date = reservation.ready_date + timedelta(
            days=policy.reservation_expiry_days
        )
        if notes:
            reservation.notes = notes
        reservation.save(
            update_fields=[
                "status",
                "ready_date",
                "expiry_date",
                "notes",
                "updated_at",
            ]
        )
        _notify_reservation_ready(reservation)
        return reservation
    if status == Reservation.EXPIRED:
        if reservation.status != Reservation.READY:
            raise ValidationError("Only ready reservations can expire.")
        reservation.status = status
        reservation.save(update_fields=["status", "updated_at"])
        promote_next_reservation(reservation.book)
        return reservation
    raise ValidationError("This reservation status transition is not allowed.")


def mark_overdue_records():
    today = timezone.localdate()
    return BorrowRecord.objects.filter(
        status=BorrowRecord.BORROWED,
        due_date__lt=today,
    ).update(status=BorrowRecord.OVERDUE, updated_at=timezone.now())


@transaction.atomic
def mark_expired_reservations():
    today = timezone.localdate()
    reservations = list(
        Reservation.objects.select_for_update().filter(
            status=Reservation.READY,
            expiry_date__lt=today,
        ).select_related("book")
    )
    if not reservations:
        return 0
    Reservation.objects.filter(pk__in=[item.pk for item in reservations]).update(
        status=Reservation.EXPIRED,
        updated_at=timezone.now(),
    )
    for book_id in {item.book_id for item in reservations}:
        promote_next_reservation(Book(pk=book_id))
    return len(reservations)


def active_borrow_queryset():
    return BorrowRecord.objects.active()

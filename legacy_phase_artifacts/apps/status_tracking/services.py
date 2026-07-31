from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import BookCopy
from apps.circulation.models import BorrowRecord
from apps.circulation.services import sync_book_status
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import BookStatusLog, DamagedBook, LostBook, RepairRecord


MONEY_ZERO = Decimal("0.00")
UNSET = object()


def _money(value):
    return Decimal(str(value or MONEY_ZERO)).quantize(Decimal("0.01"))


def _active_borrow_for_copy(book_copy):
    return (
        BorrowRecord.objects.select_for_update()
        .select_related("member__user", "book_copy__book")
        .filter(book_copy=book_copy, status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE])
        .order_by("-borrow_date", "-created_at")
        .first()
    )


def _lock_borrow_record(borrow_record):
    if not borrow_record:
        return None
    return (
        BorrowRecord.objects.select_for_update()
        .select_related("member__user", "book_copy__book")
        .get(pk=borrow_record.pk)
    )


def _validate_borrow_record(book_copy, borrow_record, member=None):
    if not borrow_record:
        return
    if borrow_record.book_copy_id != book_copy.pk:
        raise ValidationError("Borrow record must belong to the selected book copy.")
    if member and borrow_record.member_id != member.pk:
        raise ValidationError("Member must match the selected borrow record.")


def _close_active_borrow_record(borrow_record, status):
    if not borrow_record or not borrow_record.is_active:
        return
    borrow_record.status = status
    borrow_record.return_date = timezone.localdate()
    borrow_record.save(update_fields=["status", "return_date", "updated_at"])


def _create_status_fine(member, borrow_record, amount, reason, description, created_by):
    amount = _money(amount)
    if not member or amount <= MONEY_ZERO:
        return None

    from apps.fines.models import Fine
    from apps.fines.services import create_fine

    existing = (
        Fine.objects.filter(
            member=member,
            borrow_record=borrow_record,
            reason=reason,
            description=description,
        )
        .exclude(status__in=[Fine.PAID, Fine.WAIVED])
        .first()
    )
    if existing:
        return existing
    return create_fine(
        member=member,
        borrow_record=borrow_record,
        amount=amount,
        reason=reason,
        description=description,
        created_by=created_by,
    )


def log_status_change(book_copy, previous_status, new_status, reason, changed_by=None, notes=""):
    if previous_status == new_status:
        return None
    return BookStatusLog.objects.create(
        book=book_copy.book,
        book_copy=book_copy,
        previous_status=previous_status or "",
        new_status=new_status,
        reason=reason,
        notes=notes,
        changed_by=changed_by,
    )


@transaction.atomic
def set_book_copy_status(book_copy, new_status, changed_by=None, reason="Status updated", notes="", condition=None):
    book_copy = BookCopy.objects.select_for_update().select_related("book").get(pk=book_copy.pk)
    previous_status = book_copy.status
    book_copy.status = new_status
    update_fields = ["status", "updated_at"]
    if condition:
        book_copy.condition = condition
        update_fields.append("condition")
    book_copy.save(update_fields=update_fields)
    sync_book_status(book_copy.book)
    log_status_change(book_copy, previous_status, new_status, reason, changed_by=changed_by, notes=notes)
    if new_status == BookCopy.AVAILABLE:
        from apps.circulation.services import promote_next_reservation

        promote_next_reservation(book_copy.book)
    return book_copy


@transaction.atomic
def report_lost_book(book_copy, reported_by=None, borrow_record=None, member=None, replacement_cost=0, description=""):
    book_copy = BookCopy.objects.select_for_update().select_related("book").get(pk=book_copy.pk)
    borrow_record = _lock_borrow_record(borrow_record) or _active_borrow_for_copy(book_copy)
    member = member or (borrow_record.member if borrow_record else None)
    _validate_borrow_record(book_copy, borrow_record, member)

    if LostBook.objects.select_for_update().open().filter(book_copy=book_copy).exists():
        raise ValidationError("This copy already has an open lost-book record.")

    replacement_cost = _money(replacement_cost)
    record = LostBook.objects.create(
        book_copy=book_copy,
        borrow_record=borrow_record,
        member=member,
        reported_by=reported_by,
        replacement_cost=replacement_cost,
        description=description,
    )
    _close_active_borrow_record(borrow_record, BorrowRecord.LOST)
    set_book_copy_status(
        book_copy,
        BookCopy.LOST,
        changed_by=reported_by,
        reason="Book reported lost",
        notes=description,
    )

    if member:
        create_notification(
            recipient=member,
            title="Lost book recorded",
            message=f"'{book_copy.book.title}' ({book_copy.copy_code}) has been recorded as lost.",
            notification_type=Notification.LOST_BOOK,
            channel=Notification.IN_APP,
            priority=Notification.HIGH,
            related_borrow_record=borrow_record,
            related_book_copy=book_copy,
            created_by=reported_by,
            deduplication_key=f"lost-book:{record.pk}:reported",
        )
        _create_status_fine(
            member,
            borrow_record,
            replacement_cost,
            reason="lost_book",
            description=f"Replacement cost for lost book copy {book_copy.copy_code}.",
            created_by=reported_by,
        )
    return record


@transaction.atomic
def update_lost_record(
    record,
    *,
    status,
    replacement_cost,
    description,
    resolution_notes,
    resolved_date=None,
    changed_by=None,
):
    record = LostBook.objects.select_for_update().select_related("book_copy__book", "member__user").get(pk=record.pk)
    record.status = status
    record.replacement_cost = _money(replacement_cost)
    record.description = description
    record.resolution_notes = resolution_notes
    record.resolved_date = resolved_date
    record.save()

    if record.status in {LostBook.RECOVERED, LostBook.REPLACED}:
        set_book_copy_status(
            record.book_copy,
            BookCopy.AVAILABLE,
            changed_by=changed_by,
            reason="Lost book resolved",
            notes=record.resolution_notes,
            condition=BookCopy.GOOD,
        )
    elif record.status == LostBook.WRITTEN_OFF:
        set_book_copy_status(
            record.book_copy,
            BookCopy.LOST,
            changed_by=changed_by,
            reason="Lost book written off",
            notes=record.resolution_notes,
        )
    else:
        set_book_copy_status(
            record.book_copy,
            BookCopy.LOST,
            changed_by=changed_by,
            reason="Lost book still open",
            notes=record.resolution_notes,
        )
    return record


@transaction.atomic
def report_damaged_book(
    book_copy,
    reported_by=None,
    borrow_record=None,
    member=None,
    severity=DamagedBook.MINOR,
    estimated_repair_cost=0,
    description="",
):
    book_copy = BookCopy.objects.select_for_update().select_related("book").get(pk=book_copy.pk)
    borrow_record = _lock_borrow_record(borrow_record) or _active_borrow_for_copy(book_copy)
    member = member or (borrow_record.member if borrow_record else None)
    _validate_borrow_record(book_copy, borrow_record, member)

    if DamagedBook.objects.select_for_update().open().filter(book_copy=book_copy).exists():
        raise ValidationError("This copy already has an open damaged-book record.")

    estimated_repair_cost = _money(estimated_repair_cost)
    record = DamagedBook.objects.create(
        book_copy=book_copy,
        borrow_record=borrow_record,
        member=member,
        reported_by=reported_by,
        severity=severity,
        estimated_repair_cost=estimated_repair_cost,
        description=description,
    )
    _close_active_borrow_record(borrow_record, BorrowRecord.DAMAGED)
    set_book_copy_status(
        book_copy,
        BookCopy.DAMAGED,
        changed_by=reported_by,
        reason="Book reported damaged",
        notes=description,
        condition=BookCopy.DAMAGED_CONDITION,
    )
    if member:
        create_notification(
            recipient=member,
            title="Damaged book recorded",
            message=f"'{book_copy.book.title}' ({book_copy.copy_code}) has been recorded as damaged.",
            notification_type=Notification.DAMAGED_BOOK,
            channel=Notification.IN_APP,
            priority=Notification.NORMAL,
            related_borrow_record=borrow_record,
            related_book_copy=book_copy,
            created_by=reported_by,
            deduplication_key=f"damaged-book:{record.pk}:reported",
        )
        _create_status_fine(
            member,
            borrow_record,
            estimated_repair_cost,
            reason="damaged_book",
            description=f"Estimated repair cost for damaged book copy {book_copy.copy_code}.",
            created_by=reported_by,
        )
    return record


@transaction.atomic
def update_damaged_record(
    record,
    *,
    status,
    severity,
    estimated_repair_cost,
    description,
    resolution_notes,
    resolved_date=None,
    changed_by=None,
):
    record = DamagedBook.objects.select_for_update().select_related("book_copy__book", "member__user").get(pk=record.pk)
    record.status = status
    record.severity = severity
    record.estimated_repair_cost = _money(estimated_repair_cost)
    record.description = description
    record.resolution_notes = resolution_notes
    record.resolved_date = resolved_date
    record.save()

    if record.status == DamagedBook.REPAIRED:
        set_book_copy_status(
            record.book_copy,
            BookCopy.AVAILABLE,
            changed_by=changed_by,
            reason="Damaged book repaired",
            notes=record.resolution_notes,
            condition=BookCopy.GOOD,
        )
    elif record.status == DamagedBook.SENT_REPAIR:
        set_book_copy_status(
            record.book_copy,
            BookCopy.UNDER_REPAIR,
            changed_by=changed_by,
            reason="Damaged book sent to repair",
            notes=record.resolution_notes,
            condition=BookCopy.DAMAGED_CONDITION,
        )
    else:
        set_book_copy_status(
            record.book_copy,
            BookCopy.DAMAGED,
            changed_by=changed_by,
            reason="Damaged book status updated",
            notes=record.resolution_notes,
            condition=BookCopy.DAMAGED_CONDITION,
        )
    return record


@transaction.atomic
def create_repair_record(book_copy, sent_by=None, damage_record=None, vendor="", expected_return_date=None, repair_cost=0, notes=""):
    book_copy = BookCopy.objects.select_for_update().select_related("book").get(pk=book_copy.pk)
    if RepairRecord.objects.select_for_update().open().filter(book_copy=book_copy).exists():
        raise ValidationError("This copy already has an open repair record.")

    if damage_record:
        damage_record = DamagedBook.objects.select_for_update().select_related("book_copy__book").get(pk=damage_record.pk)
        if damage_record.book_copy_id != book_copy.pk:
            raise ValidationError("Damage record must belong to the selected book copy.")
    else:
        damage_record = DamagedBook.objects.select_for_update().open().filter(book_copy=book_copy).first()
        if not damage_record:
            damage_record = DamagedBook.objects.create(
                book_copy=book_copy,
                reported_by=sent_by,
                severity=DamagedBook.MODERATE,
                description=notes,
                status=DamagedBook.SENT_REPAIR,
            )

    repair = RepairRecord.objects.create(
        book_copy=book_copy,
        damage_record=damage_record,
        sent_by=sent_by,
        vendor=vendor,
        expected_return_date=expected_return_date,
        repair_cost=_money(repair_cost),
        notes=notes,
    )
    if damage_record.status != DamagedBook.SENT_REPAIR:
        damage_record.status = DamagedBook.SENT_REPAIR
        damage_record.save(update_fields=["status", "resolved_date", "updated_at"])
    set_book_copy_status(
        book_copy,
        BookCopy.UNDER_REPAIR,
        changed_by=sent_by,
        reason="Book sent for repair",
        notes=notes,
        condition=BookCopy.DAMAGED_CONDITION,
    )
    return repair


@transaction.atomic
def update_repair_status(
    repair,
    status,
    changed_by=None,
    completed_date=None,
    notes="",
    vendor=None,
    expected_return_date=UNSET,
    repair_cost=None,
):
    repair = RepairRecord.objects.select_for_update().select_related("book_copy__book", "damage_record").get(pk=repair.pk)
    repair.status = status
    if vendor is not None:
        repair.vendor = vendor
    if expected_return_date is not UNSET:
        repair.expected_return_date = expected_return_date
    if repair_cost is not None:
        repair.repair_cost = _money(repair_cost)
    if notes is not None:
        repair.notes = notes
    repair.completed_date = completed_date
    repair.save()

    if status == RepairRecord.COMPLETED:
        if repair.damage_record:
            repair.damage_record.status = DamagedBook.REPAIRED
            repair.damage_record.resolution_notes = notes or repair.damage_record.resolution_notes
            repair.damage_record.resolved_date = repair.completed_date
            repair.damage_record.save(update_fields=["status", "resolution_notes", "resolved_date", "updated_at"])
        set_book_copy_status(
            repair.book_copy,
            BookCopy.AVAILABLE,
            changed_by=changed_by,
            reason="Repair completed",
            notes=repair.notes,
            condition=BookCopy.GOOD,
        )
    elif status == RepairRecord.CANCELLED:
        if repair.damage_record and repair.damage_record.status == DamagedBook.SENT_REPAIR:
            repair.damage_record.status = DamagedBook.UNDER_REVIEW
            repair.damage_record.save(update_fields=["status", "resolved_date", "updated_at"])
        set_book_copy_status(
            repair.book_copy,
            BookCopy.DAMAGED,
            changed_by=changed_by,
            reason="Repair cancelled",
            notes=repair.notes,
            condition=BookCopy.DAMAGED_CONDITION,
        )
    else:
        if repair.damage_record and repair.damage_record.status != DamagedBook.SENT_REPAIR:
            repair.damage_record.status = DamagedBook.SENT_REPAIR
            repair.damage_record.save(update_fields=["status", "resolved_date", "updated_at"])
        set_book_copy_status(
            repair.book_copy,
            BookCopy.UNDER_REPAIR,
            changed_by=changed_by,
            reason="Repair status updated",
            notes=repair.notes,
            condition=BookCopy.DAMAGED_CONDITION,
        )
    return repair

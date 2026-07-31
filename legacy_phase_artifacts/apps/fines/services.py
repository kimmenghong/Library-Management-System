from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.circulation.models import BorrowRecord
from apps.members.models import Member

from .models import Fine, Payment


@transaction.atomic
def create_fine(
    *,
    member,
    amount,
    reason,
    created_by,
    borrow_record=None,
    description="",
):
    member = Member.objects.select_for_update().get(pk=member.pk)
    if borrow_record:
        borrow_record = BorrowRecord.objects.select_for_update().get(pk=borrow_record.pk)
        if borrow_record.member_id != member.pk:
            raise ValidationError("Fine member must match the borrow record member.")
    amount = Decimal(amount)
    if amount <= Decimal("0.00"):
        raise ValidationError("Fine amount must be greater than zero.")
    return Fine.objects.create(
        member=member,
        borrow_record=borrow_record,
        amount=amount,
        reason=reason,
        description=description,
        created_by=created_by,
        updated_by=created_by,
    )


@transaction.atomic
def update_fine(*, fine, amount, reason, description, updated_by):
    fine = Fine.objects.select_for_update().get(pk=fine.pk)
    if fine.status == Fine.WAIVED:
        raise ValidationError("Waived fines cannot be edited.")
    if fine.payments.exists():
        raise ValidationError("A fine with payment history cannot be edited.")
    fine.amount = Decimal(amount)
    fine.reason = reason
    fine.description = description
    fine.updated_by = updated_by
    fine.save()
    return fine


@transaction.atomic
def waive_fine(*, fine, waived_by, reason):
    fine = Fine.objects.select_for_update().get(pk=fine.pk)
    if not fine.is_outstanding:
        raise ValidationError("Only outstanding fines can be waived.")
    reason = reason.strip()
    if not reason:
        raise ValidationError("A waiver reason is required.")
    fine.status = Fine.WAIVED
    fine.waived_by = waived_by
    fine.waived_at = timezone.now()
    fine.waiver_reason = reason
    fine.updated_by = waived_by
    fine.save()
    return fine


def record_payment(
    *,
    fine,
    amount_paid,
    payment_method,
    payment_date,
    received_by,
    reference_number="",
    notes="",
):
    return Payment.objects.create(
        fine=fine,
        member=fine.member,
        amount_paid=amount_paid,
        payment_method=payment_method,
        payment_date=payment_date,
        reference_number=reference_number,
        notes=notes,
        received_by=received_by,
    )


@transaction.atomic
def void_payment(*, payment, voided_by, reason):
    payment = Payment.objects.select_for_update().select_related("fine").get(pk=payment.pk)
    Fine.objects.select_for_update().get(pk=payment.fine_id)
    if payment.status == Payment.VOIDED:
        raise ValidationError("This payment is already voided.")
    reason = reason.strip()
    if not reason:
        raise ValidationError("A void reason is required.")
    payment.status = Payment.VOIDED
    payment.voided_by = voided_by
    payment.voided_at = timezone.now()
    payment.void_reason = reason
    payment.save(update_fields=["status", "voided_by", "voided_at", "void_reason", "updated_at"])
    return payment

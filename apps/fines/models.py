from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from apps.members.models import Member


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FineQuerySet(models.QuerySet):
    def outstanding(self):
        return self.filter(status__in=[Fine.UNPAID, Fine.PARTIAL])

    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(member__user=user)


class Fine(TimeStampedModel):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    WAIVED = "waived"

    STATUS_CHOICES = [
        (UNPAID, "Unpaid"),
        (PARTIAL, "Partially Paid"),
        (PAID, "Paid"),
        (WAIVED, "Waived"),
    ]

    LATE_RETURN = "late_return"
    DAMAGED_BOOK = "damaged_book"
    LOST_BOOK = "lost_book"
    OTHER = "other"

    REASON_CHOICES = [
        (LATE_RETURN, "Late Return"),
        (DAMAGED_BOOK, "Damaged Book"),
        (LOST_BOOK, "Lost Book"),
        (OTHER, "Other"),
    ]

    borrow_record = models.ForeignKey(
        "circulation.BorrowRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fines",
    )
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="fines")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default=LATE_RETURN)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=UNPAID,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_fines",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_fines",
    )
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waived_fines",
        editable=False,
    )
    waived_at = models.DateTimeField(null=True, blank=True, editable=False)
    waiver_reason = models.TextField(blank=True, editable=False)

    objects = FineQuerySet.as_manager()

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["member", "status"]),
            models.Index(fields=["reason", "status"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="fine_amount_positive"),
            models.CheckConstraint(
                condition=Q(paid_amount__gte=0) & Q(paid_amount__lte=F("amount")),
                name="fine_paid_amount_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="unpaid", paid_amount=0, waived_at__isnull=True)
                    | (
                        Q(status="partial", paid_amount__gt=0, waived_at__isnull=True)
                        & Q(paid_amount__lt=F("amount"))
                    )
                    | Q(status="paid", paid_amount=F("amount"), waived_at__isnull=True)
                    | (
                        Q(status="waived", waived_at__isnull=False)
                        & ~Q(waiver_reason="")
                    )
                ),
                name="fine_status_matches_accounting",
            ),
            models.UniqueConstraint(
                fields=["borrow_record"],
                condition=Q(reason="late_return", borrow_record__isnull=False),
                name="one_late_fine_per_borrow",
            ),
        ]

    def clean(self):
        errors = {}
        if self.borrow_record_id and self.member_id:
            if self.borrow_record.member_id != self.member_id:
                errors["member"] = "Fine member must match the borrow record member."
        if self.reason == self.LATE_RETURN and not self.borrow_record_id:
            errors["borrow_record"] = "Late-return fines require a borrow record."
        if self.amount is not None and self.amount <= Decimal("0.00"):
            errors["amount"] = "Fine amount must be greater than zero."
        if self.paid_amount is not None and self.amount is not None:
            if self.paid_amount < Decimal("0.00") or self.paid_amount > self.amount:
                errors["paid_amount"] = "Paid amount must be between zero and the fine amount."

        if self.status == self.WAIVED:
            if not self.waived_at or not self.waiver_reason.strip():
                errors["status"] = "Waived fines require a timestamp and reason."
        elif self.waived_at or self.waived_by_id or self.waiver_reason:
            errors["status"] = "Only waived fines can contain waiver details."

        if self.pk:
            previous = Fine.objects.filter(pk=self.pk).values(
                "amount", "member_id", "borrow_record_id", "reason", "status"
            ).first()
            if previous:
                protected_changed = any(
                    [
                        previous["amount"] != self.amount,
                        previous["member_id"] != self.member_id,
                        previous["borrow_record_id"] != self.borrow_record_id,
                        previous["reason"] != self.reason,
                    ]
                )
                if protected_changed and self.payments.exists():
                    errors["amount"] = "A fine with payment history cannot be financially edited."
                if previous["status"] == self.WAIVED and self.status != self.WAIVED:
                    errors["status"] = "A waived fine cannot be reopened."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.description = self.description.strip()
        self.waiver_reason = self.waiver_reason.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def balance(self):
        if self.status == self.WAIVED:
            return Decimal("0.00")
        return max(self.amount - self.paid_amount, Decimal("0.00"))

    @property
    def is_outstanding(self):
        return self.status in {self.UNPAID, self.PARTIAL}

    def sync_payment_totals(self):
        total = self.payments.filter(status=Payment.COMPLETED).aggregate(
            total=Sum("amount_paid")
        )["total"] or Decimal("0.00")
        total = min(total, self.amount)
        if self.status == self.WAIVED:
            status = self.WAIVED
        elif total <= Decimal("0.00"):
            status = self.UNPAID
        elif total < self.amount:
            status = self.PARTIAL
        else:
            status = self.PAID
        Fine.objects.filter(pk=self.pk).update(
            paid_amount=total,
            status=status,
            updated_at=timezone.now(),
        )
        self.paid_amount = total
        self.status = status
        return total

    def update_payment_status(self):
        """Compatibility wrapper for older integrations."""
        self.sync_payment_totals()

    def __str__(self):
        return f"{self.member.member_code} - {self.amount} ({self.get_status_display()})"


class PaymentQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=Payment.COMPLETED)

    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(member__user=user)


class Payment(TimeStampedModel):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_PAYMENT = "mobile_payment"
    OTHER = "other"

    PAYMENT_METHOD_CHOICES = [
        (CASH, "Cash"),
        (CARD, "Card"),
        (BANK_TRANSFER, "Bank Transfer"),
        (MOBILE_PAYMENT, "Mobile Payment"),
        (OTHER, "Other"),
    ]

    COMPLETED = "completed"
    VOIDED = "voided"
    STATUS_CHOICES = [
        (COMPLETED, "Completed"),
        (VOIDED, "Voided"),
    ]

    fine = models.ForeignKey(Fine, on_delete=models.PROTECT, related_name="payments")
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="fine_payments",
        editable=False,
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default=CASH,
    )
    payment_date = models.DateField(default=timezone.localdate)
    reference_number = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=COMPLETED,
        editable=False,
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_fine_payments",
    )
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="voided_fine_payments",
        editable=False,
    )
    voided_at = models.DateTimeField(null=True, blank=True, editable=False)
    void_reason = models.TextField(blank=True, editable=False)

    objects = PaymentQuerySet.as_manager()

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["member", "payment_date"]),
            models.Index(fields=["fine", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_paid__gt=0),
                name="payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="completed", voided_at__isnull=True, void_reason="")
                    | (
                        Q(status="voided", voided_at__isnull=False)
                        & ~Q(void_reason="")
                    )
                ),
                name="payment_status_matches_void",
            ),
        ]

    def clean(self):
        errors = {}
        if self.fine_id and self.member_id and self.member_id != self.fine.member_id:
            errors["member"] = "Payment member must match the fine member."
        if self.amount_paid is not None and self.amount_paid <= Decimal("0.00"):
            errors["amount_paid"] = "Payment amount must be greater than zero."
        if self.payment_date and self.payment_date > timezone.localdate():
            errors["payment_date"] = "Payment date cannot be in the future."
        if self.status == self.VOIDED:
            if not self.voided_at or not self.void_reason.strip():
                errors["status"] = "Voided payments require a timestamp and reason."
        elif self.voided_at or self.voided_by_id or self.void_reason:
            errors["status"] = "Only voided payments can contain void details."

        if self.pk:
            previous = Payment.objects.filter(pk=self.pk).values(
                "fine_id",
                "member_id",
                "amount_paid",
                "payment_method",
                "payment_date",
                "reference_number",
                "notes",
                "status",
            ).first()
            if previous:
                immutable_changed = any(
                    previous[field] != getattr(self, field)
                    for field in (
                        "fine_id",
                        "member_id",
                        "amount_paid",
                        "payment_method",
                        "payment_date",
                        "reference_number",
                        "notes",
                    )
                )
                if immutable_changed:
                    errors["status"] = "Completed payment details are immutable."
                if previous["status"] == self.VOIDED and self.status != self.VOIDED:
                    errors["status"] = "A voided payment cannot be restored."
                if previous["status"] == self.COMPLETED and self.status not in {
                    self.COMPLETED,
                    self.VOIDED,
                }:
                    errors["status"] = "Invalid payment status transition."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.reference_number = self.reference_number.strip()
        self.notes = self.notes.strip()
        self.void_reason = self.void_reason.strip()
        with transaction.atomic():
            fine = Fine.objects.select_for_update().get(pk=self.fine_id)
            self.fine = fine
            self.member = fine.member
            is_new = self.pk is None
            if is_new:
                if not fine.is_outstanding:
                    raise ValidationError("Payments can only be recorded against outstanding fines.")
                current_total = fine.payments.completed().aggregate(total=Sum("amount_paid"))[
                    "total"
                ] or Decimal("0.00")
                remaining = fine.amount - current_total
                if self.amount_paid > remaining:
                    raise ValidationError(
                        {"amount_paid": f"Payment cannot exceed remaining balance: {remaining}."}
                    )
                self.status = self.COMPLETED
                self.voided_by = None
                self.voided_at = None
                self.void_reason = ""
            self.full_clean()
            super().save(*args, **kwargs)
            fine.sync_payment_totals()

    def delete(self, *args, **kwargs):
        raise ValidationError("Payment records cannot be deleted; void the payment instead.")

    @property
    def effective_amount(self):
        return self.amount_paid if self.status == self.COMPLETED else Decimal("0.00")

    def __str__(self):
        return f"{self.member.member_code} paid {self.amount_paid}"

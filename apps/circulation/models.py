from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Book, BookCopy
from apps.members.models import Member


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BorrowingPolicy(TimeStampedModel):
    member_type = models.CharField(max_length=30, choices=Member.MEMBER_TYPE_CHOICES, unique=True)
    max_books = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1)])
    loan_period_days = models.PositiveSmallIntegerField(default=14, validators=[MinValueValidator(1)])
    renewal_days = models.PositiveSmallIntegerField(default=7, validators=[MinValueValidator(1)])
    max_renewals = models.PositiveSmallIntegerField(default=1)
    fine_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    reservation_expiry_days = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["member_type"]
        verbose_name_plural = "Borrowing policies"
        constraints = [
            models.CheckConstraint(condition=Q(max_books__gte=1), name="policy_max_books_positive"),
            models.CheckConstraint(condition=Q(loan_period_days__gte=1), name="policy_loan_days_positive"),
            models.CheckConstraint(condition=Q(renewal_days__gte=1), name="policy_renewal_days_positive"),
            models.CheckConstraint(condition=Q(fine_per_day__gte=0), name="policy_fine_non_negative"),
            models.CheckConstraint(
                condition=Q(reservation_expiry_days__gte=1),
                name="policy_reservation_expiry_positive",
            ),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_member_type_display()} policy"


class BorrowRecordQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE])

    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(member__user=user)


class BorrowRecord(TimeStampedModel):
    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"
    DAMAGED = "damaged"

    STATUS_CHOICES = [
        (BORROWED, "Borrowed"),
        (RETURNED, "Returned"),
        (OVERDUE, "Overdue"),
        (LOST, "Lost"),
        (DAMAGED, "Damaged"),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="borrow_records")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="borrow_records")
    borrowed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issued_borrow_records",
    )
    borrow_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=BORROWED,
        editable=False,
    )
    renewal_count = models.PositiveSmallIntegerField(default=0, editable=False)
    fine_rate_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("1.00"),
        editable=False,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    notes = models.TextField(blank=True)

    objects = BorrowRecordQuerySet.as_manager()

    class Meta:
        ordering = ["-borrow_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["member", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(due_date__gte=models.F("borrow_date")),
                name="borrow_due_on_or_after_borrow",
            ),
            models.CheckConstraint(
                condition=Q(return_date__isnull=True)
                | Q(return_date__gte=models.F("borrow_date")),
                name="borrow_return_on_or_after_borrow",
            ),
            models.CheckConstraint(
                condition=Q(fine_rate_per_day__gte=0),
                name="borrow_fine_rate_non_negative",
            ),
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(status__in=["borrowed", "overdue"]),
                name="one_active_borrow_per_copy",
            ),
        ]

    def clean(self):
        errors = {}
        if self.due_date and self.borrow_date and self.due_date < self.borrow_date:
            errors["due_date"] = "Due date cannot be earlier than borrow date."
        if self.return_date and self.borrow_date and self.return_date < self.borrow_date:
            errors["return_date"] = "Return date cannot be earlier than borrow date."
        if self.status in {self.BORROWED, self.OVERDUE} and self.return_date:
            errors["return_date"] = "An active borrow record cannot have a return date."
        if self.status == self.RETURNED and not self.return_date:
            errors["return_date"] = "A returned borrow record requires a return date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in {self.BORROWED, self.OVERDUE}

    @property
    def days_late(self):
        check_date = self.return_date or timezone.localdate()
        if check_date <= self.due_date:
            return 0
        return (check_date - self.due_date).days

    @property
    def estimated_fine(self):
        return self.fine_rate_per_day * self.days_late

    def refresh_overdue_status(self):
        if self.status == self.BORROWED and timezone.localdate() > self.due_date:
            self.status = self.OVERDUE
            self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.member.member_code} borrowed {self.book_copy.copy_code}"


class ReturnRecord(TimeStampedModel):
    GOOD = "good"
    DAMAGED = "damaged"
    LOST = "lost"
    UNDER_REPAIR = "under_repair"

    CONDITION_CHOICES = [
        (GOOD, "Good"),
        (DAMAGED, "Damaged"),
        (LOST, "Lost"),
        (UNDER_REPAIR, "Under Repair"),
    ]

    borrow_record = models.OneToOneField(
        BorrowRecord,
        on_delete=models.PROTECT,
        related_name="return_record",
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_returns",
    )
    return_date = models.DateField(default=timezone.localdate)
    book_condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, default=GOOD)
    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-return_date", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(fine_amount__gte=0), name="return_fine_non_negative")
        ]

    def clean(self):
        if (
            self.borrow_record_id
            and self.return_date
            and self.return_date < self.borrow_record.borrow_date
        ):
            raise ValidationError(
                {"return_date": "Return date cannot be earlier than borrow date."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Return for {self.borrow_record.book_copy.copy_code}"


class RenewalRecord(TimeStampedModel):
    borrow_record = models.ForeignKey(
        BorrowRecord,
        on_delete=models.PROTECT,
        related_name="renewals",
    )
    renewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_renewals",
    )
    old_due_date = models.DateField()
    new_due_date = models.DateField()
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(new_due_date__gt=models.F("old_due_date")),
                name="renewal_new_due_after_old_due",
            )
        ]

    def clean(self):
        if self.old_due_date and self.new_due_date and self.new_due_date <= self.old_due_date:
            raise ValidationError({"new_due_date": "New due date must be after the old due date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.borrow_record.book_copy.copy_code}: {self.old_due_date} to {self.new_due_date}"


class ReservationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=[Reservation.PENDING, Reservation.READY])

    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(member__user=user)


class Reservation(TimeStampedModel):
    PENDING = "pending"
    READY = "ready"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (READY, "Ready for Pickup"),
        (FULFILLED, "Fulfilled"),
        (CANCELLED, "Cancelled"),
        (EXPIRED, "Expired"),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="reservations")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="reservations")
    reserved_date = models.DateField(default=timezone.localdate)
    ready_date = models.DateField(null=True, blank=True, editable=False)
    expiry_date = models.DateField(null=True, blank=True, editable=False)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=PENDING,
        editable=False,
    )
    notes = models.TextField(blank=True)

    objects = ReservationQuerySet.as_manager()

    class Meta:
        ordering = ["status", "reserved_date", "created_at"]
        indexes = [
            models.Index(fields=["book", "status"]),
            models.Index(fields=["member", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(expiry_date__isnull=True)
                | Q(expiry_date__gte=models.F("reserved_date")),
                name="reservation_expiry_on_or_after_reserved",
            ),
            models.CheckConstraint(
                condition=Q(ready_date__isnull=True)
                | Q(ready_date__gte=models.F("reserved_date")),
                name="reservation_ready_on_or_after_reserved",
            ),
            models.UniqueConstraint(
                fields=["member", "book"],
                condition=Q(status__in=["pending", "ready"]),
                name="one_active_reservation_per_member_book",
            ),
            models.UniqueConstraint(
                fields=["book"],
                condition=Q(status="ready"),
                name="one_ready_reservation_per_book",
            ),
        ]

    def clean(self):
        errors = {}
        if self.expiry_date and self.expiry_date < self.reserved_date:
            errors["expiry_date"] = "Expiry date cannot be earlier than reservation date."
        if self.ready_date and self.ready_date < self.reserved_date:
            errors["ready_date"] = "Ready date cannot be earlier than reservation date."
        if self.status == self.PENDING and (self.ready_date or self.expiry_date):
            errors["status"] = "Pending reservations cannot have pickup dates."
        if self.status == self.READY and (not self.ready_date or not self.expiry_date):
            errors["status"] = "Ready reservations require ready and expiry dates."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in {self.PENDING, self.READY}

    @property
    def queue_position(self):
        if self.status != self.PENDING:
            return None
        return (
            Reservation.objects.filter(
                book=self.book,
                status=self.PENDING,
                created_at__lt=self.created_at,
            ).count()
            + 1
        )

    def __str__(self):
        return f"{self.member.member_code} reserved {self.book.title}"

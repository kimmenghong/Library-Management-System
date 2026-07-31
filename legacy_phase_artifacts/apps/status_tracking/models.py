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


class BookStatusLogQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.none()


class BookStatusLog(TimeStampedModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="status_logs")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name="status_logs")
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, choices=BookCopy.STATUS_CHOICES)
    reason = models.CharField(max_length=160)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="book_status_changes",
    )

    objects = BookStatusLogQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["book_copy", "created_at"]),
            models.Index(fields=["new_status", "created_at"]),
        ]

    def clean(self):
        errors = {}
        if self.book_copy_id and self.book_id and self.book_copy.book_id != self.book_id:
            errors["book"] = "Status log book must match the selected book copy."
        if not self.reason.strip():
            errors["reason"] = "A reason is required for status tracking."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.reason = self.reason.strip()
        self.notes = self.notes.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book_copy.copy_code}: {self.previous_status or '-'} to {self.new_status}"


class LostBookQuerySet(models.QuerySet):
    def open(self):
        return self.filter(status__in=LostBook.OPEN_STATUSES)

    def resolved(self):
        return self.filter(status__in=LostBook.RESOLVED_STATUSES)


class LostBook(TimeStampedModel):
    REPORTED = "reported"
    CHARGED = "charged"
    PAID = "paid"
    REPLACED = "replaced"
    RECOVERED = "recovered"
    WRITTEN_OFF = "written_off"

    OPEN_STATUSES = [REPORTED, CHARGED, PAID]
    RESOLVED_STATUSES = [REPLACED, RECOVERED, WRITTEN_OFF]

    STATUS_CHOICES = [
        (REPORTED, "Reported"),
        (CHARGED, "Charged"),
        (PAID, "Paid"),
        (REPLACED, "Replaced"),
        (RECOVERED, "Recovered"),
        (WRITTEN_OFF, "Written Off"),
    ]

    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="lost_records")
    borrow_record = models.ForeignKey(
        "circulation.BorrowRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lost_records",
    )
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="lost_books")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reported_lost_books",
    )
    reported_date = models.DateField(default=timezone.localdate)
    replacement_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=REPORTED)
    description = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)

    objects = LostBookQuerySet.as_manager()

    class Meta:
        ordering = ["status", "-reported_date"]
        indexes = [
            models.Index(fields=["book_copy", "status"]),
            models.Index(fields=["member", "status"]),
            models.Index(fields=["reported_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(replacement_cost__gte=0),
                name="lost_replacement_cost_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status__in=["replaced", "recovered", "written_off"], resolved_date__isnull=False)
                    | Q(status__in=["reported", "charged", "paid"], resolved_date__isnull=True)
                ),
                name="lost_status_matches_resolved_date",
            ),
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(status__in=["reported", "charged", "paid"]),
                name="one_open_lost_record_per_copy",
            ),
        ]

    @property
    def is_resolved(self):
        return self.status in self.RESOLVED_STATUSES

    def clean(self):
        errors = {}
        today = timezone.localdate()
        if self.reported_date and self.reported_date > today:
            errors["reported_date"] = "Reported date cannot be in the future."
        if self.resolved_date:
            if self.resolved_date > today:
                errors["resolved_date"] = "Resolved date cannot be in the future."
            if self.reported_date and self.resolved_date < self.reported_date:
                errors["resolved_date"] = "Resolved date cannot be earlier than reported date."
        if self.replacement_cost is not None and self.replacement_cost < Decimal("0.00"):
            errors["replacement_cost"] = "Replacement cost cannot be negative."
        if self.borrow_record_id:
            if self.book_copy_id and self.borrow_record.book_copy_id != self.book_copy_id:
                errors["borrow_record"] = "Borrow record must belong to the selected book copy."
            if self.member_id and self.borrow_record.member_id != self.member_id:
                errors["member"] = "Member must match the selected borrow record."
        if self.status in self.RESOLVED_STATUSES and not self.resolved_date:
            errors["resolved_date"] = "Resolved lost-book records require a resolved date."
        if self.status in self.OPEN_STATUSES and self.resolved_date:
            errors["resolved_date"] = "Open lost-book records cannot have a resolved date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.description = self.description.strip()
        self.resolution_notes = self.resolution_notes.strip()
        if self.status in self.RESOLVED_STATUSES and not self.resolved_date:
            self.resolved_date = timezone.localdate()
        if self.status in self.OPEN_STATUSES:
            self.resolved_date = None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lost {self.book_copy.copy_code}"


class DamagedBookQuerySet(models.QuerySet):
    def open(self):
        return self.filter(status__in=DamagedBook.OPEN_STATUSES)

    def resolved(self):
        return self.filter(status__in=DamagedBook.RESOLVED_STATUSES)


class DamagedBook(TimeStampedModel):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"

    SEVERITY_CHOICES = [
        (MINOR, "Minor"),
        (MODERATE, "Moderate"),
        (SEVERE, "Severe"),
    ]

    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    SENT_REPAIR = "sent_repair"
    REPAIRED = "repaired"
    WRITTEN_OFF = "written_off"

    OPEN_STATUSES = [REPORTED, UNDER_REVIEW, SENT_REPAIR]
    RESOLVED_STATUSES = [REPAIRED, WRITTEN_OFF]

    STATUS_CHOICES = [
        (REPORTED, "Reported"),
        (UNDER_REVIEW, "Under Review"),
        (SENT_REPAIR, "Sent to Repair"),
        (REPAIRED, "Repaired"),
        (WRITTEN_OFF, "Written Off"),
    ]

    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="damage_records")
    borrow_record = models.ForeignKey(
        "circulation.BorrowRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="damage_records",
    )
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="damaged_books")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reported_damaged_books",
    )
    reported_date = models.DateField(default=timezone.localdate)
    severity = models.CharField(max_length=30, choices=SEVERITY_CHOICES, default=MINOR)
    estimated_repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=REPORTED)
    description = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)

    objects = DamagedBookQuerySet.as_manager()

    class Meta:
        ordering = ["status", "-reported_date"]
        indexes = [
            models.Index(fields=["book_copy", "status"]),
            models.Index(fields=["member", "status"]),
            models.Index(fields=["severity", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(estimated_repair_cost__gte=0),
                name="damaged_estimated_cost_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status__in=["repaired", "written_off"], resolved_date__isnull=False)
                    | Q(status__in=["reported", "under_review", "sent_repair"], resolved_date__isnull=True)
                ),
                name="damaged_status_matches_resolved_date",
            ),
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(status__in=["reported", "under_review", "sent_repair"]),
                name="one_open_damage_record_per_copy",
            ),
        ]

    @property
    def is_resolved(self):
        return self.status in self.RESOLVED_STATUSES

    def clean(self):
        errors = {}
        today = timezone.localdate()
        if self.reported_date and self.reported_date > today:
            errors["reported_date"] = "Reported date cannot be in the future."
        if self.resolved_date:
            if self.resolved_date > today:
                errors["resolved_date"] = "Resolved date cannot be in the future."
            if self.reported_date and self.resolved_date < self.reported_date:
                errors["resolved_date"] = "Resolved date cannot be earlier than reported date."
        if self.estimated_repair_cost is not None and self.estimated_repair_cost < Decimal("0.00"):
            errors["estimated_repair_cost"] = "Estimated repair cost cannot be negative."
        if self.borrow_record_id:
            if self.book_copy_id and self.borrow_record.book_copy_id != self.book_copy_id:
                errors["borrow_record"] = "Borrow record must belong to the selected book copy."
            if self.member_id and self.borrow_record.member_id != self.member_id:
                errors["member"] = "Member must match the selected borrow record."
        if self.status in self.RESOLVED_STATUSES and not self.resolved_date:
            errors["resolved_date"] = "Resolved damaged-book records require a resolved date."
        if self.status in self.OPEN_STATUSES and self.resolved_date:
            errors["resolved_date"] = "Open damaged-book records cannot have a resolved date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.description = self.description.strip()
        self.resolution_notes = self.resolution_notes.strip()
        if self.status in self.RESOLVED_STATUSES and not self.resolved_date:
            self.resolved_date = timezone.localdate()
        if self.status in self.OPEN_STATUSES:
            self.resolved_date = None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Damaged {self.book_copy.copy_code}"


class RepairRecordQuerySet(models.QuerySet):
    def open(self):
        return self.filter(status=RepairRecord.UNDER_REPAIR)

    def completed(self):
        return self.filter(status=RepairRecord.COMPLETED)


class RepairRecord(TimeStampedModel):
    UNDER_REPAIR = "under_repair"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (UNDER_REPAIR, "Under Repair"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="repair_records")
    damage_record = models.ForeignKey(
        DamagedBook,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repair_records",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_repair_records",
    )
    vendor = models.CharField(max_length=160, blank=True)
    sent_date = models.DateField(default=timezone.localdate)
    expected_return_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=UNDER_REPAIR)
    notes = models.TextField(blank=True)

    objects = RepairRecordQuerySet.as_manager()

    class Meta:
        ordering = ["status", "-sent_date"]
        indexes = [
            models.Index(fields=["book_copy", "status"]),
            models.Index(fields=["sent_date"]),
            models.Index(fields=["expected_return_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(repair_cost__gte=0),
                name="repair_cost_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="completed", completed_date__isnull=False)
                    | Q(status__in=["under_repair", "cancelled"], completed_date__isnull=True)
                ),
                name="repair_status_matches_completed_date",
            ),
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(status="under_repair"),
                name="one_open_repair_record_per_copy",
            ),
        ]

    def clean(self):
        errors = {}
        today = timezone.localdate()
        if self.sent_date and self.sent_date > today:
            errors["sent_date"] = "Sent date cannot be in the future."
        if self.expected_return_date and self.sent_date and self.expected_return_date < self.sent_date:
            errors["expected_return_date"] = "Expected return date cannot be earlier than sent date."
        if self.completed_date:
            if self.completed_date > today:
                errors["completed_date"] = "Completed date cannot be in the future."
            if self.sent_date and self.completed_date < self.sent_date:
                errors["completed_date"] = "Completed date cannot be earlier than sent date."
        if self.status == self.COMPLETED and not self.completed_date:
            errors["completed_date"] = "Completed repairs require a completed date."
        if self.status != self.COMPLETED and self.completed_date:
            errors["completed_date"] = "Only completed repairs can have a completed date."
        if self.repair_cost is not None and self.repair_cost < Decimal("0.00"):
            errors["repair_cost"] = "Repair cost cannot be negative."
        if self.damage_record_id and self.book_copy_id and self.damage_record.book_copy_id != self.book_copy_id:
            errors["damage_record"] = "Damage record must belong to the selected book copy."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.vendor = self.vendor.strip()
        self.notes = self.notes.strip()
        if self.status == self.COMPLETED and not self.completed_date:
            self.completed_date = timezone.localdate()
        if self.status != self.COMPLETED:
            self.completed_date = None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repair {self.book_copy.copy_code}"

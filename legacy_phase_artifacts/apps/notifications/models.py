from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import BookCopy
from apps.members.models import Member


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NotificationQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(recipient__user=user)

    def unread(self):
        return self.filter(status=Notification.UNREAD)


class Notification(TimeStampedModel):
    DUE_DATE = "due_date"
    OVERDUE = "overdue"
    RESERVATION = "reservation"
    FINE = "fine"
    LOST_BOOK = "lost_book"
    DAMAGED_BOOK = "damaged_book"
    REPAIR = "repair"
    SYSTEM = "system"

    TYPE_CHOICES = [
        (DUE_DATE, "Due Date Reminder"),
        (OVERDUE, "Overdue Book"),
        (RESERVATION, "Reservation"),
        (FINE, "Fine"),
        (LOST_BOOK, "Lost Book"),
        (DAMAGED_BOOK, "Damaged Book"),
        (REPAIR, "Repair"),
        (SYSTEM, "System"),
    ]

    IN_APP = "in_app"
    EMAIL = "email"
    BOTH = "both"
    CHANNEL_CHOICES = [
        (IN_APP, "In-App"),
        (EMAIL, "Email"),
        (BOTH, "In-App and Email"),
    ]

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    PRIORITY_CHOICES = [(LOW, "Low"), (NORMAL, "Normal"), (HIGH, "High")]

    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    STATUS_CHOICES = [(UNREAD, "Unread"), (READ, "Read"), (ARCHIVED, "Archived")]

    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=SYSTEM)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=IN_APP)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=NORMAL)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=UNREAD,
        editable=False,
    )
    related_borrow_record = models.ForeignKey(
        "circulation.BorrowRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    related_book_copy = models.ForeignKey(
        BookCopy,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    deduplication_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        editable=False,
    )
    is_email_sent = models.BooleanField(default=False, editable=False)
    email_sent_at = models.DateTimeField(null=True, blank=True, editable=False)
    read_at = models.DateTimeField(null=True, blank=True, editable=False)
    archived_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_notifications",
    )

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(status="unread", read_at__isnull=True, archived_at__isnull=True)
                    | Q(status="read", read_at__isnull=False, archived_at__isnull=True)
                    | Q(status="archived", archived_at__isnull=False)
                ),
                name="notification_status_dates_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_email_sent=False, email_sent_at__isnull=True)
                    | Q(is_email_sent=True, email_sent_at__isnull=False)
                ),
                name="notification_email_flag_valid",
            ),
        ]

    def clean(self):
        errors = {}
        if not self.title.strip():
            errors["title"] = "Notification title is required."
        if not self.message.strip():
            errors["message"] = "Notification message is required."
        if self.related_borrow_record_id:
            if self.recipient_id != self.related_borrow_record.member_id:
                errors["recipient"] = "Recipient must match the related borrow record member."
            if (
                self.related_book_copy_id
                and self.related_book_copy_id != self.related_borrow_record.book_copy_id
            ):
                errors["related_book_copy"] = "Book copy must match the related borrow record."
        if self.status == self.UNREAD and (self.read_at or self.archived_at):
            errors["status"] = "Unread notifications cannot have read or archive timestamps."
        if self.status == self.READ and (not self.read_at or self.archived_at):
            errors["status"] = "Read notifications require only a read timestamp."
        if self.status == self.ARCHIVED and not self.archived_at:
            errors["status"] = "Archived notifications require an archive timestamp."
        if self.is_email_sent != bool(self.email_sent_at):
            errors["is_email_sent"] = "Email delivery flag and timestamp must agree."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.message = self.message.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def mark_read(self):
        if self.status == self.UNREAD:
            self.status = self.READ
            self.read_at = timezone.now()
            self.archived_at = None
            self.save(update_fields=["status", "read_at", "archived_at", "updated_at"])
        return self

    def archive(self):
        self.status = self.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])
        return self

    def __str__(self):
        return f"{self.recipient.member_code} - {self.title}"


class EmailReminderQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser or user.has_role(
            "super_admin", "admin", "librarian", "assistant_librarian"
        ):
            return self
        return self.filter(member__user=user)


class EmailReminder(TimeStampedModel):
    DUE_DATE = "due_date"
    OVERDUE = "overdue"
    MANUAL = "manual"
    TYPE_CHOICES = [(DUE_DATE, "Due Date"), (OVERDUE, "Overdue"), (MANUAL, "Manual")]

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    STATUS_CHOICES = [(PENDING, "Pending"), (SENT, "Sent"), (FAILED, "Failed")]

    notification = models.ForeignKey(
        Notification,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_logs",
    )
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="email_reminders")
    borrow_record = models.ForeignKey(
        "circulation.BorrowRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_reminders",
    )
    reminder_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    email_to = models.EmailField(blank=True)
    subject = models.CharField(max_length=180)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        editable=False,
    )
    attempt_number = models.PositiveSmallIntegerField(
        default=1,
        editable=False,
        validators=[MinValueValidator(1)],
    )
    attempted_at = models.DateTimeField(default=timezone.now, editable=False)
    sent_at = models.DateTimeField(null=True, blank=True, editable=False)
    error_message = models.TextField(blank=True, editable=False)

    objects = EmailReminderQuerySet.as_manager()

    class Meta:
        ordering = ["-attempted_at", "-created_at"]
        indexes = [
            models.Index(fields=["member", "status"]),
            models.Index(fields=["status", "attempted_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(attempt_number__gte=1),
                name="email_attempt_number_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="pending", sent_at__isnull=True, error_message="")
                    | Q(status="sent", sent_at__isnull=False, error_message="")
                    | (
                        Q(status="failed", sent_at__isnull=True)
                        & ~Q(error_message="")
                    )
                ),
                name="email_attempt_status_valid",
            ),
            models.UniqueConstraint(
                fields=["notification", "attempt_number"],
                condition=Q(notification__isnull=False),
                name="unique_email_attempt_per_notification",
            ),
        ]

    def clean(self):
        errors = {}
        if self.notification_id and self.member_id != self.notification.recipient_id:
            errors["member"] = "Email member must match the notification recipient."
        if self.borrow_record_id and self.member_id != self.borrow_record.member_id:
            errors["member"] = "Email member must match the borrow record member."
        if not self.subject.strip():
            errors["subject"] = "Email subject is required."
        if not self.message.strip():
            errors["message"] = "Email message is required."
        if self.status == self.PENDING and (self.sent_at or self.error_message):
            errors["status"] = "Pending attempts cannot contain a result."
        elif self.status == self.SENT and (not self.sent_at or self.error_message):
            errors["status"] = "Sent attempts require a sent timestamp and no error."
        elif self.status == self.FAILED and (self.sent_at or not self.error_message.strip()):
            errors["status"] = "Failed attempts require an error and no sent timestamp."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.email_to = self.email_to.strip().lower()
        self.subject = self.subject.strip()
        self.message = self.message.strip()
        self.error_message = self.error_message.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Email delivery attempts cannot be deleted.")

    def __str__(self):
        return f"{self.email_to or 'No email'} - {self.subject}"

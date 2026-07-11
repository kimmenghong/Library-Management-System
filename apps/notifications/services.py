from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.circulation.models import BorrowRecord
from apps.circulation.services import mark_overdue_records

from .models import EmailReminder, Notification


def _create_notification_record(**values):
    deduplication_key = values.get("deduplication_key")
    if deduplication_key:
        defaults = values.copy()
        defaults.pop("deduplication_key")
        return Notification.objects.get_or_create(
            deduplication_key=deduplication_key,
            defaults=defaults,
        )
    return Notification.objects.create(**values), True


def create_notification(
    recipient,
    title,
    message,
    notification_type=Notification.SYSTEM,
    channel=Notification.IN_APP,
    priority=Notification.NORMAL,
    related_borrow_record=None,
    related_book_copy=None,
    created_by=None,
    send_email=False,
    deduplication_key=None,
):
    if send_email and channel == Notification.IN_APP:
        channel = Notification.BOTH
    if related_borrow_record and not related_book_copy:
        related_book_copy = related_borrow_record.book_copy
    notification, created = _create_notification_record(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        channel=channel,
        priority=priority,
        related_borrow_record=related_borrow_record,
        related_book_copy=related_book_copy,
        created_by=created_by,
        deduplication_key=deduplication_key,
    )
    notification._was_created = created
    if created and channel in {Notification.EMAIL, Notification.BOTH}:
        send_notification_email(notification)
    return notification


def _email_type_for_notification(notification):
    if notification.notification_type == Notification.DUE_DATE:
        return EmailReminder.DUE_DATE
    if notification.notification_type == Notification.OVERDUE:
        return EmailReminder.OVERDUE
    return EmailReminder.MANUAL


def _begin_email_attempt(notification):
    with transaction.atomic():
        notification = Notification.objects.select_for_update().select_related(
            "recipient__user", "related_borrow_record"
        ).get(pk=notification.pk)
        sent = notification.email_logs.filter(status=EmailReminder.SENT).order_by(
            "-attempt_number"
        ).first()
        if notification.is_email_sent and sent:
            return notification, sent, False

        pending = notification.email_logs.filter(status=EmailReminder.PENDING).order_by(
            "-attempt_number"
        ).first()
        timeout_minutes = getattr(settings, "EMAIL_PENDING_TIMEOUT_MINUTES", 15)
        stale_before = timezone.now() - timedelta(minutes=timeout_minutes)
        if pending and pending.attempted_at >= stale_before:
            return notification, pending, False
        if pending:
            EmailReminder.objects.filter(pk=pending.pk).update(
                status=EmailReminder.FAILED,
                sent_at=None,
                error_message="Delivery worker timed out before reporting a result.",
                updated_at=timezone.now(),
            )

        attempt_number = (
            notification.email_logs.aggregate(maximum=Max("attempt_number"))["maximum"] or 0
        ) + 1
        attempt = EmailReminder.objects.create(
            notification=notification,
            member=notification.recipient,
            borrow_record=notification.related_borrow_record,
            reminder_type=_email_type_for_notification(notification),
            email_to=notification.recipient.user.email,
            subject=notification.title,
            message=notification.message,
            status=EmailReminder.PENDING,
            attempt_number=attempt_number,
        )
        return notification, attempt, True


def send_notification_email(notification):
    notification, attempt, should_send = _begin_email_attempt(notification)
    if not should_send:
        return attempt

    if not attempt.email_to:
        EmailReminder.objects.filter(pk=attempt.pk).update(
            status=EmailReminder.FAILED,
            sent_at=None,
            error_message="Member does not have an email address.",
            updated_at=timezone.now(),
        )
        attempt.refresh_from_db()
        return attempt

    try:
        delivered = send_mail(
            subject=attempt.subject,
            message=attempt.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[attempt.email_to],
            fail_silently=False,
        )
        if delivered != 1:
            raise RuntimeError("Email backend did not confirm delivery.")
    except Exception as exc:
        EmailReminder.objects.filter(pk=attempt.pk).update(
            status=EmailReminder.FAILED,
            sent_at=None,
            error_message=str(exc)[:2000] or "Unknown email delivery error.",
            updated_at=timezone.now(),
        )
        attempt.refresh_from_db()
        return attempt

    delivered_at = timezone.now()
    with transaction.atomic():
        EmailReminder.objects.filter(pk=attempt.pk).update(
            status=EmailReminder.SENT,
            sent_at=delivered_at,
            error_message="",
            updated_at=delivered_at,
        )
        Notification.objects.filter(pk=notification.pk).update(
            is_email_sent=True,
            email_sent_at=delivered_at,
            updated_at=delivered_at,
        )
    attempt.refresh_from_db()
    return attempt


def retry_notification_email(notification):
    notification = Notification.objects.get(pk=notification.pk)
    if notification.is_email_sent:
        raise ValidationError("This notification email has already been sent.")
    if notification.channel not in {Notification.EMAIL, Notification.BOTH}:
        raise ValidationError("This notification is not configured for email delivery.")
    return send_notification_email(notification)


def send_due_date_notifications(days=3, created_by=None, send_email=True):
    if days < 0 or days > 30:
        raise ValidationError("Due-date reminder window must be between 0 and 30 days.")
    today = timezone.localdate()
    end_date = today + timedelta(days=days)
    records = BorrowRecord.objects.select_related(
        "member__user", "book_copy__book"
    ).filter(status=BorrowRecord.BORROWED, due_date__range=(today, end_date))
    created = []
    for record in records:
        days_left = (record.due_date - today).days
        title = "Book due today" if days_left == 0 else f"Book due in {days_left} day(s)"
        notification = create_notification(
            recipient=record.member,
            title=title,
            message=(
                f"Reminder: '{record.book_copy.book.title}' "
                f"({record.book_copy.copy_code}) is due on {record.due_date}."
            ),
            notification_type=Notification.DUE_DATE,
            channel=Notification.BOTH if send_email else Notification.IN_APP,
            priority=Notification.NORMAL,
            related_borrow_record=record,
            created_by=created_by,
            deduplication_key=f"due:{record.pk}:{today.isoformat()}",
        )
        if notification._was_created:
            created.append(notification)
    return created


def send_overdue_notifications(created_by=None, send_email=True):
    mark_overdue_records()
    today = timezone.localdate()
    records = BorrowRecord.objects.select_related(
        "member__user", "book_copy__book"
    ).filter(status=BorrowRecord.OVERDUE)
    created = []
    for record in records:
        days_late = record.days_late
        notification = create_notification(
            recipient=record.member,
            title=f"Overdue book: {record.book_copy.book.title}",
            message=(
                f"'{record.book_copy.book.title}' ({record.book_copy.copy_code}) "
                f"is overdue by {days_late} day(s). Please return it as soon as possible."
            ),
            notification_type=Notification.OVERDUE,
            channel=Notification.BOTH if send_email else Notification.IN_APP,
            priority=Notification.HIGH,
            related_borrow_record=record,
            created_by=created_by,
            deduplication_key=f"overdue:{record.pk}:{today.isoformat()}",
        )
        if notification._was_created:
            created.append(notification)
    return created

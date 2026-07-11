from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.catalog.models import Book, BookCopy
from apps.circulation.models import BorrowRecord
from apps.circulation.services import borrow_book
from apps.members.models import Member

from .forms import ManualNotificationForm, ReminderRunForm
from .models import EmailReminder, Notification
from .services import (
    create_notification,
    retry_notification_email,
    send_due_date_notifications,
    send_notification_email,
    send_overdue_notifications,
)


User = get_user_model()


class NotificationTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.student_role = Role.objects.get(slug=Role.STUDENT)
        cls.teacher_role = Role.objects.get(slug=Role.TEACHER)
        cls.librarian_role = Role.objects.get(slug=Role.LIBRARIAN)
        cls.librarian = User.objects.create_user(
            username="notification_librarian",
            email="notification.librarian@example.com",
            password="StrongPass123!",
            role=cls.librarian_role,
            first_name="Notification",
            last_name="Librarian",
        )
        cls.student_user = User.objects.create_user(
            username="notification_student",
            email="notification.student@example.com",
            password="StrongPass123!",
            role=cls.student_role,
            first_name="Notification",
            last_name="Student",
        )
        cls.teacher_user = User.objects.create_user(
            username="notification_teacher",
            email="notification.teacher@example.com",
            password="StrongPass123!",
            role=cls.teacher_role,
            first_name="Notification",
            last_name="Teacher",
        )
        cls.superuser = User.objects.create_superuser(
            username="notification_root",
            email="notification.root@example.com",
            password="StrongPass123!",
        )
        cls.student = Member.objects.create(
            user=cls.student_user,
            member_type=Member.STUDENT,
        )
        cls.teacher = Member.objects.create(
            user=cls.teacher_user,
            member_type=Member.TEACHER,
        )
        cls.book_due = Book.objects.create(title="Due Date Systems", book_code="NOTIFY-001")
        cls.copy_due = BookCopy.objects.create(book=cls.book_due, barcode="NOTIFY-COPY-001")
        cls.book_overdue = Book.objects.create(
            title="Overdue Workflows",
            book_code="NOTIFY-002",
        )
        cls.copy_overdue = BookCopy.objects.create(
            book=cls.book_overdue,
            barcode="NOTIFY-COPY-002",
        )

    def make_notification(self, member=None, **kwargs):
        return create_notification(
            recipient=member or self.student,
            title=kwargs.pop("title", "Library message"),
            message=kwargs.pop("message", "Your library account has an update."),
            created_by=kwargs.pop("created_by", self.librarian),
            **kwargs,
        )

    def make_due_loan(self):
        return borrow_book(
            self.student,
            self.copy_due,
            self.librarian,
            due_date=timezone.localdate() + timedelta(days=2),
        )

    def make_overdue_loan(self):
        today = timezone.localdate()
        return borrow_book(
            self.student,
            self.copy_overdue,
            self.librarian,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
        )


class NotificationModelTests(NotificationTestDataMixin, TestCase):
    def test_related_loan_must_match_recipient_and_copy(self):
        loan = self.make_due_loan()
        with self.assertRaisesMessage(ValidationError, "Recipient must match"):
            Notification.objects.create(
                recipient=self.teacher,
                title="Wrong recipient",
                message="Mismatch",
                related_borrow_record=loan,
                related_book_copy=self.copy_due,
            )

    def test_read_and_archive_transitions_have_audit_dates(self):
        notification = self.make_notification()
        notification.mark_read()
        self.assertEqual(notification.status, Notification.READ)
        self.assertIsNotNone(notification.read_at)
        notification.archive()
        self.assertEqual(notification.status, Notification.ARCHIVED)
        self.assertIsNotNone(notification.archived_at)

    def test_member_visibility_is_private(self):
        own = self.make_notification()
        other = self.make_notification(member=self.teacher)
        visible = Notification.objects.visible_to(self.student_user)
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)

    def test_email_attempts_cannot_be_deleted(self):
        notification = self.make_notification(channel=Notification.BOTH)
        attempt = notification.email_logs.get()
        with self.assertRaisesMessage(ValidationError, "cannot be deleted"):
            attempt.delete()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationServiceTests(NotificationTestDataMixin, TestCase):
    def test_both_channel_creates_successful_email_attempt(self):
        notification = self.make_notification(channel=Notification.BOTH)
        notification.refresh_from_db()
        attempt = notification.email_logs.get()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(attempt.status, EmailReminder.SENT)
        self.assertEqual(attempt.attempt_number, 1)
        self.assertTrue(notification.is_email_sent)
        self.assertIsNotNone(notification.email_sent_at)

    def test_missing_email_creates_failed_attempt(self):
        user = User.objects.create_user(
            username="notification_no_email",
            email="",
            password="StrongPass123!",
            role=self.student_role,
        )
        member = Member.objects.create(user=user, member_type=Member.STUDENT)
        notification = self.make_notification(member=member, channel=Notification.EMAIL)
        attempt = notification.email_logs.get()
        self.assertEqual(attempt.status, EmailReminder.FAILED)
        self.assertEqual(attempt.email_to, "")
        self.assertIn("does not have", attempt.error_message)

    def test_failed_delivery_can_be_retried_as_second_attempt(self):
        with patch("apps.notifications.services.send_mail", side_effect=RuntimeError("SMTP down")):
            notification = self.make_notification(channel=Notification.BOTH)
        first = notification.email_logs.get()
        self.assertEqual(first.status, EmailReminder.FAILED)

        second = retry_notification_email(notification)
        notification.refresh_from_db()
        self.assertEqual(second.status, EmailReminder.SENT)
        self.assertEqual(second.attempt_number, 2)
        self.assertEqual(notification.email_logs.count(), 2)
        self.assertTrue(notification.is_email_sent)

    def test_pending_attempt_suppresses_duplicate_worker(self):
        notification = self.make_notification(channel=Notification.IN_APP)
        notification.channel = Notification.BOTH
        notification.save(update_fields=["channel", "updated_at"])
        pending = EmailReminder.objects.create(
            notification=notification,
            member=self.student,
            reminder_type=EmailReminder.MANUAL,
            email_to=self.student_user.email,
            subject=notification.title,
            message=notification.message,
        )
        result = send_notification_email(notification)
        self.assertEqual(result.pk, pending.pk)
        self.assertEqual(notification.email_logs.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_due_date_reminders_are_idempotent_per_day(self):
        self.make_due_loan()
        first = send_due_date_notifications(days=3, send_email=False)
        second = send_due_date_notifications(days=3, send_email=False)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        self.assertEqual(Notification.objects.filter(notification_type=Notification.DUE_DATE).count(), 1)

    def test_overdue_service_updates_loan_and_sends_alert(self):
        loan = self.make_overdue_loan()
        created = send_overdue_notifications(send_email=True)
        loan.refresh_from_db()
        self.assertEqual(loan.status, BorrowRecord.OVERDUE)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].priority, Notification.HIGH)
        self.assertEqual(created[0].email_logs.get().status, EmailReminder.SENT)

    def test_due_window_is_validated(self):
        with self.assertRaisesMessage(ValidationError, "between 0 and 30"):
            send_due_date_notifications(days=31)


class NotificationFormTests(NotificationTestDataMixin, TestCase):
    def test_manual_form_rejects_mismatched_recipient(self):
        loan = self.make_due_loan()
        form = ManualNotificationForm(
            data={
                "recipient": self.teacher.pk,
                "title": "Mismatch",
                "message": "Wrong member",
                "notification_type": Notification.SYSTEM,
                "channel": Notification.IN_APP,
                "priority": Notification.NORMAL,
                "related_borrow_record": loan.pk,
                "related_book_copy": self.copy_due.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("recipient", form.errors)

    def test_reminder_form_requires_a_selected_type(self):
        form = ReminderRunForm(
            data={
                "due_within_days": 3,
                "send_due_date_reminders": "",
                "send_overdue_reminders": "",
                "send_email": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationViewTests(NotificationTestDataMixin, TestCase):
    def test_member_cannot_view_or_mark_another_members_notification(self):
        own = self.make_notification()
        other = self.make_notification(member=self.teacher)
        self.client.force_login(self.student_user)

        list_response = self.client.get(reverse("notifications:notification_list"))
        self.assertContains(list_response, own.title)
        self.assertNotContains(list_response, self.teacher.member_code)
        self.assertEqual(
            self.client.get(
                reverse("notifications:notification_detail", kwargs={"pk": other.pk})
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("notifications:notification_mark_read", kwargs={"pk": other.pk})
            ).status_code,
            404,
        )
        other.refresh_from_db()
        self.assertEqual(other.status, Notification.UNREAD)

    def test_member_history_rejects_another_member(self):
        self.client.force_login(self.student_user)
        response = self.client.get(
            reverse("notifications:member_history", kwargs={"member_pk": self.teacher.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read_updates_only_visible_notifications(self):
        own = self.make_notification()
        other = self.make_notification(member=self.teacher)
        self.client.force_login(self.student_user)
        response = self.client.post(reverse("notifications:notification_mark_all_read"))
        self.assertRedirects(response, reverse("notifications:notification_list"))
        own.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(own.status, Notification.READ)
        self.assertEqual(other.status, Notification.UNREAD)

    def test_librarian_can_send_email_notification_from_form(self):
        self.client.force_login(self.librarian)
        response = self.client.post(
            reverse("notifications:notification_create"),
            {
                "recipient": self.student.pk,
                "title": "Desk notice",
                "message": "Your requested material is ready.",
                "notification_type": Notification.SYSTEM,
                "channel": Notification.BOTH,
                "priority": Notification.NORMAL,
                "related_borrow_record": "",
                "related_book_copy": "",
            },
        )
        notification = Notification.objects.get(title="Desk notice")
        self.assertRedirects(
            response,
            reverse("notifications:notification_detail", kwargs={"pk": notification.pk}),
        )
        self.assertEqual(notification.email_logs.get().status, EmailReminder.SENT)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationAPITests(NotificationTestDataMixin, APITestCase):
    def test_member_api_is_scoped_and_can_mark_own_message_read(self):
        own = self.make_notification()
        other = self.make_notification(member=self.teacher)
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/notifications/")
        payload = response.data.get("results", response.data)
        self.assertEqual({item["id"] for item in payload}, {own.pk})

        read_response = self.client.post(f"/api/notifications/{own.pk}/read/")
        self.assertEqual(read_response.status_code, 200)
        own.refresh_from_db()
        self.assertEqual(own.status, Notification.READ)
        self.assertEqual(
            self.client.post(f"/api/notifications/{other.pk}/read/").status_code,
            404,
        )

    def test_api_create_sends_email_and_disallows_patch(self):
        self.client.force_authenticate(self.librarian)
        response = self.client.post(
            "/api/notifications/",
            {
                "recipient": self.student.pk,
                "title": "API email",
                "message": "Sent through the API workflow.",
                "notification_type": Notification.SYSTEM,
                "channel": Notification.BOTH,
                "priority": Notification.NORMAL,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        notification = Notification.objects.get(pk=response.data["id"])
        self.assertTrue(notification.is_email_sent)
        patch_response = self.client.patch(
            f"/api/notifications/{notification.pk}/",
            {"status": Notification.ARCHIVED},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 405)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ReminderCommandTests(NotificationTestDataMixin, TestCase):
    def test_management_command_is_repeatable(self):
        self.make_due_loan()
        output = StringIO()
        call_command("send_library_reminders", "--days=3", "--no-email", stdout=output)
        call_command("send_library_reminders", "--days=3", "--no-email", stdout=output)
        self.assertEqual(Notification.objects.filter(notification_type=Notification.DUE_DATE).count(), 1)
        self.assertIn("Created 0 due-date", output.getvalue())

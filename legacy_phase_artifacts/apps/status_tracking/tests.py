from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.catalog.models import Book, BookCopy
from apps.circulation.models import BorrowingPolicy, BorrowRecord
from apps.circulation.services import borrow_book
from apps.fines.models import Fine
from apps.members.models import Member
from apps.notifications.models import Notification

from .forms import LostBookForm, RepairRecordForm
from .models import BookStatusLog, DamagedBook, LostBook, RepairRecord
from .services import (
    create_repair_record,
    report_damaged_book,
    report_lost_book,
    update_damaged_record,
    update_lost_record,
    update_repair_status,
)


User = get_user_model()


class StatusTrackingTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.librarian_role = Role.objects.get(slug=Role.LIBRARIAN)
        cls.student_role = Role.objects.get(slug=Role.STUDENT)

        cls.librarian = User.objects.create_user(
            username="status_librarian",
            email="status.librarian@example.com",
            password="StrongPass123!",
            role=cls.librarian_role,
            is_staff=True,
        )
        cls.student_user = User.objects.create_user(
            username="status_student",
            email="status.student@example.com",
            password="StrongPass123!",
            first_name="Status",
            last_name="Student",
            role=cls.student_role,
        )
        cls.other_student_user = User.objects.create_user(
            username="status_other_student",
            email="status.other.student@example.com",
            password="StrongPass123!",
            first_name="Other",
            last_name="Student",
            role=cls.student_role,
        )
        cls.member = Member.objects.create(user=cls.student_user, member_type=Member.STUDENT)
        cls.other_member = Member.objects.create(user=cls.other_student_user, member_type=Member.STUDENT)

        policy = BorrowingPolicy.objects.get(member_type=Member.STUDENT)
        policy.max_books = 5
        policy.loan_period_days = 14
        policy.renewal_days = 7
        policy.max_renewals = 1
        policy.fine_per_day = Decimal("1.00")
        policy.is_active = True
        policy.save()

        cls.book = Book.objects.create(title="Status Tracking Handbook", book_code="STATUS-001")
        cls.second_book = Book.objects.create(title="Repair Desk Manual", book_code="STATUS-002")
        cls.copy = BookCopy.objects.create(book=cls.book, barcode="STATUS-COPY-001")
        cls.second_copy = BookCopy.objects.create(book=cls.second_book, barcode="STATUS-COPY-002")

    def issue(self, member=None, book_copy=None):
        return borrow_book(
            member=member or self.member,
            book_copy=book_copy or self.copy,
            borrowed_by=self.librarian,
            borrow_date=timezone.localdate() - timedelta(days=2),
        )


class StatusTrackingModelTests(StatusTrackingTestDataMixin, TestCase):
    def test_lost_record_rejects_borrow_record_for_different_copy(self):
        loan = self.issue(book_copy=self.copy)
        record = LostBook(
            book_copy=self.second_copy,
            borrow_record=loan,
            member=self.member,
            replacement_cost=Decimal("20.00"),
        )
        with self.assertRaisesMessage(ValidationError, "Borrow record must belong"):
            record.full_clean()

    def test_completed_repair_requires_coherent_dates(self):
        damage = DamagedBook.objects.create(book_copy=self.copy, reported_by=self.librarian)
        repair = RepairRecord(
            book_copy=self.copy,
            damage_record=damage,
            status=RepairRecord.COMPLETED,
            sent_date=timezone.localdate(),
            completed_date=timezone.localdate() - timedelta(days=1),
        )
        with self.assertRaisesMessage(ValidationError, "Completed date cannot be earlier"):
            repair.full_clean()


class StatusTrackingServiceTests(StatusTrackingTestDataMixin, TestCase):
    def test_report_lost_book_updates_copy_borrow_fine_notification_and_log(self):
        loan = self.issue()
        record = report_lost_book(
            self.copy,
            reported_by=self.librarian,
            borrow_record=loan,
            replacement_cost=Decimal("25.00"),
            description="Missing after semester inventory.",
        )

        self.copy.refresh_from_db()
        loan.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(record.member, self.member)
        self.assertEqual(self.copy.status, BookCopy.LOST)
        self.assertEqual(self.book.status, Book.LOST)
        self.assertEqual(loan.status, BorrowRecord.LOST)
        self.assertEqual(loan.return_date, timezone.localdate())
        self.assertTrue(BookStatusLog.objects.filter(book_copy=self.copy, new_status=BookCopy.LOST).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.member, notification_type=Notification.LOST_BOOK).exists())
        fine = Fine.objects.get(member=self.member, reason=Fine.LOST_BOOK)
        self.assertEqual(fine.amount, Decimal("25.00"))

    def test_duplicate_open_lost_record_is_rejected(self):
        report_lost_book(self.copy, reported_by=self.librarian, member=self.member)
        with self.assertRaisesMessage(ValidationError, "already has an open lost-book record"):
            report_lost_book(self.copy, reported_by=self.librarian, member=self.member)

    def test_recovered_lost_book_returns_copy_to_available(self):
        record = report_lost_book(self.copy, reported_by=self.librarian, member=self.member)
        update_lost_record(
            record,
            status=LostBook.RECOVERED,
            replacement_cost=Decimal("0.00"),
            description=record.description,
            resolution_notes="Recovered during shelf audit.",
            changed_by=self.librarian,
        )
        self.copy.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(record.status, LostBook.RECOVERED)
        self.assertEqual(record.resolved_date, timezone.localdate())
        self.assertEqual(self.copy.status, BookCopy.AVAILABLE)

    def test_report_damaged_book_updates_copy_condition_and_fine(self):
        loan = self.issue()
        record = report_damaged_book(
            self.copy,
            reported_by=self.librarian,
            borrow_record=loan,
            severity=DamagedBook.SEVERE,
            estimated_repair_cost=Decimal("12.50"),
            description="Water damaged pages.",
        )
        self.copy.refresh_from_db()
        loan.refresh_from_db()

        self.assertEqual(record.status, DamagedBook.REPORTED)
        self.assertEqual(self.copy.status, BookCopy.DAMAGED)
        self.assertEqual(self.copy.condition, BookCopy.DAMAGED_CONDITION)
        self.assertEqual(loan.status, BorrowRecord.DAMAGED)
        fine = Fine.objects.get(member=self.member, reason=Fine.DAMAGED_BOOK)
        self.assertEqual(fine.amount, Decimal("12.50"))

    def test_repair_flow_sets_under_repair_then_available(self):
        damage = report_damaged_book(self.copy, reported_by=self.librarian, member=self.member)
        repair = create_repair_record(
            self.copy,
            sent_by=self.librarian,
            damage_record=damage,
            vendor="Campus Bindery",
            expected_return_date=timezone.localdate() + timedelta(days=5),
            repair_cost=Decimal("8.00"),
            notes="Binding replacement.",
        )
        self.copy.refresh_from_db()
        damage.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.UNDER_REPAIR)
        self.assertEqual(damage.status, DamagedBook.SENT_REPAIR)

        update_repair_status(
            repair,
            RepairRecord.COMPLETED,
            changed_by=self.librarian,
            completed_date=timezone.localdate(),
            notes="Repair complete.",
        )
        self.copy.refresh_from_db()
        damage.refresh_from_db()
        repair.refresh_from_db()
        self.assertEqual(repair.status, RepairRecord.COMPLETED)
        self.assertEqual(damage.status, DamagedBook.REPAIRED)
        self.assertEqual(self.copy.status, BookCopy.AVAILABLE)
        self.assertEqual(self.copy.condition, BookCopy.GOOD)

    def test_repair_without_damage_record_creates_damage_record(self):
        repair = create_repair_record(self.copy, sent_by=self.librarian, notes="Loose binding found.")
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.UNDER_REPAIR)
        self.assertIsNotNone(repair.damage_record)
        self.assertEqual(repair.damage_record.status, DamagedBook.SENT_REPAIR)

    def test_written_off_damage_keeps_copy_unavailable(self):
        damage = report_damaged_book(self.copy, reported_by=self.librarian, member=self.member)
        update_damaged_record(
            damage,
            status=DamagedBook.WRITTEN_OFF,
            severity=damage.severity,
            estimated_repair_cost=damage.estimated_repair_cost,
            description=damage.description,
            resolution_notes="Too damaged to circulate.",
            changed_by=self.librarian,
        )
        self.copy.refresh_from_db()
        damage.refresh_from_db()
        self.assertEqual(damage.resolved_date, timezone.localdate())
        self.assertEqual(self.copy.status, BookCopy.DAMAGED)


class StatusTrackingFormTests(StatusTrackingTestDataMixin, TestCase):
    def test_lost_book_form_rejects_mismatched_borrow_record(self):
        loan = self.issue(book_copy=self.copy)
        form = LostBookForm(
            data={
                "book_copy": self.second_copy.pk,
                "borrow_record": loan.pk,
                "member": self.member.pk,
                "replacement_cost": "10.00",
                "description": "Mismatch attempt.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Borrow record must belong", str(form.errors))

    def test_repair_form_rejects_damage_record_for_other_copy(self):
        damage = report_damaged_book(self.copy, reported_by=self.librarian, member=self.member)
        form = RepairRecordForm(
            data={
                "book_copy": self.second_copy.pk,
                "damage_record": damage.pk,
                "vendor": "Campus Bindery",
                "expected_return_date": timezone.localdate() + timedelta(days=3),
                "repair_cost": "5.00",
                "notes": "Mismatch attempt.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Damage record must belong", str(form.errors))


class StatusTrackingViewTests(StatusTrackingTestDataMixin, TestCase):
    def test_librarian_can_create_lost_record_from_view(self):
        self.client.force_login(self.librarian)
        loan = self.issue()
        response = self.client.post(
            reverse("status_tracking:lost_create"),
            {
                "book_copy": self.copy.pk,
                "borrow_record": loan.pk,
                "member": self.member.pk,
                "replacement_cost": "18.00",
                "description": "Lost during checkout.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.LOST)

    def test_student_without_status_permission_is_redirected(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("status_tracking:lost_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("accounts:dashboard")))


class StatusTrackingAPITests(StatusTrackingTestDataMixin, APITestCase):
    def test_api_create_damaged_record_uses_service_logic(self):
        self.client.force_authenticate(self.librarian)
        response = self.client.post(
            "/api/damaged-books/",
            {
                "book_copy": self.copy.pk,
                "member": self.member.pk,
                "severity": DamagedBook.MODERATE,
                "estimated_repair_cost": "9.00",
                "description": "API damage report.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.DAMAGED)
        self.assertTrue(BookStatusLog.objects.filter(book_copy=self.copy, new_status=BookCopy.DAMAGED).exists())

    def test_api_complete_repair_updates_copy_status(self):
        self.client.force_authenticate(self.librarian)
        damage = report_damaged_book(self.copy, reported_by=self.librarian, member=self.member)
        repair = create_repair_record(self.copy, sent_by=self.librarian, damage_record=damage)
        response = self.client.patch(
            f"/api/repair-records/{repair.pk}/",
            {
                "status": RepairRecord.COMPLETED,
                "completed_date": timezone.localdate().isoformat(),
                "notes": "Completed through API.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.copy.refresh_from_db()
        damage.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.AVAILABLE)
        self.assertEqual(damage.status, DamagedBook.REPAIRED)

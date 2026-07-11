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
from apps.fines.models import Fine
from apps.members.models import Member
from apps.notifications.models import Notification
from apps.status_tracking.models import DamagedBook

from .forms import ReservationForm, ReturnBookForm
from .models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord
from .services import (
    borrow_book,
    mark_expired_reservations,
    renew_borrow,
    reserve_book,
    return_book,
    update_reservation_status,
)


User = get_user_model()


class CirculationTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.student_role = Role.objects.get(slug=Role.STUDENT)
        cls.teacher_role = Role.objects.get(slug=Role.TEACHER)
        cls.librarian_role = Role.objects.get(slug=Role.LIBRARIAN)

        cls.librarian_user = User.objects.create_user(
            username="circulation_librarian",
            email="circulation.librarian@example.com",
            password="StrongPass123!",
            role=cls.librarian_role,
            is_staff=True,
        )
        cls.student_user = User.objects.create_user(
            username="circulation_student",
            email="circulation.student@example.com",
            password="StrongPass123!",
            first_name="Circulation",
            last_name="Student",
            role=cls.student_role,
        )
        cls.second_student_user = User.objects.create_user(
            username="circulation_student_two",
            email="circulation.student.two@example.com",
            password="StrongPass123!",
            first_name="Second",
            last_name="Student",
            role=cls.student_role,
        )
        cls.teacher_user = User.objects.create_user(
            username="circulation_teacher",
            email="circulation.teacher@example.com",
            password="StrongPass123!",
            first_name="Circulation",
            last_name="Teacher",
            role=cls.teacher_role,
        )
        cls.superuser = User.objects.create_superuser(
            username="circulation_root",
            email="circulation.root@example.com",
            password="StrongPass123!",
        )

        cls.student = Member.objects.create(
            user=cls.student_user,
            member_type=Member.STUDENT,
        )
        cls.second_student = Member.objects.create(
            user=cls.second_student_user,
            member_type=Member.STUDENT,
        )
        cls.teacher = Member.objects.create(
            user=cls.teacher_user,
            member_type=Member.TEACHER,
        )

        cls.student_policy = BorrowingPolicy.objects.get(member_type=Member.STUDENT)
        cls.student_policy.max_books = 3
        cls.student_policy.loan_period_days = 14
        cls.student_policy.renewal_days = 7
        cls.student_policy.max_renewals = 1
        cls.student_policy.fine_per_day = Decimal("2.00")
        cls.student_policy.reservation_expiry_days = 2
        cls.student_policy.is_active = True
        cls.student_policy.save()

        cls.book_one = Book.objects.create(
            title="Circulation Systems",
            book_code="CIRC-001",
        )
        cls.book_two = Book.objects.create(
            title="Reliable Django Services",
            book_code="CIRC-002",
        )
        cls.book_three = Book.objects.create(
            title="Database Transactions",
            book_code="CIRC-003",
        )
        cls.copy_one = BookCopy.objects.create(book=cls.book_one, barcode="CIRC-COPY-001")
        cls.copy_two = BookCopy.objects.create(book=cls.book_two, barcode="CIRC-COPY-002")
        cls.copy_three = BookCopy.objects.create(book=cls.book_three, barcode="CIRC-COPY-003")

    def issue(self, member=None, book_copy=None, **kwargs):
        return borrow_book(
            member=member or self.student,
            book_copy=book_copy or self.copy_one,
            borrowed_by=self.librarian_user,
            **kwargs,
        )


class CirculationModelTests(CirculationTestDataMixin, TestCase):
    def test_policy_rejects_zero_limits(self):
        self.student_policy.max_books = 0
        with self.assertRaises(ValidationError):
            self.student_policy.save()

    def test_borrow_record_rejects_invalid_dates(self):
        today = timezone.localdate()
        with self.assertRaisesMessage(ValidationError, "Due date cannot be earlier"):
            BorrowRecord.objects.create(
                member=self.student,
                book_copy=self.copy_one,
                borrow_date=today,
                due_date=today - timedelta(days=1),
            )

    def test_only_one_active_loan_can_reference_a_copy(self):
        first = self.issue()
        with self.assertRaises(ValidationError):
            BorrowRecord.objects.create(
                member=self.second_student,
                book_copy=first.book_copy,
                due_date=timezone.localdate() + timedelta(days=7),
            )

    def test_only_one_ready_reservation_is_allowed_per_title(self):
        today = timezone.localdate()
        Reservation.objects.create(
            member=self.student,
            book=self.book_one,
            status=Reservation.READY,
            ready_date=today,
            expiry_date=today + timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            Reservation.objects.create(
                member=self.teacher,
                book=self.book_one,
                status=Reservation.READY,
                ready_date=today,
                expiry_date=today + timedelta(days=2),
            )

    def test_pending_reservation_queue_positions_are_stable(self):
        first = Reservation.objects.create(member=self.student, book=self.book_one)
        second = Reservation.objects.create(member=self.teacher, book=self.book_one)
        self.assertEqual(first.queue_position, 1)
        self.assertEqual(second.queue_position, 2)


class CirculationServiceTests(CirculationTestDataMixin, TestCase):
    def test_borrow_applies_policy_and_updates_copy_status(self):
        loan = self.issue()
        self.copy_one.refresh_from_db()
        self.book_one.refresh_from_db()
        self.assertEqual(
            loan.due_date,
            loan.borrow_date + timedelta(days=self.student_policy.loan_period_days),
        )
        self.assertEqual(loan.fine_rate_per_day, Decimal("2.00"))
        self.assertEqual(self.copy_one.status, BookCopy.BORROWED)
        self.assertEqual(self.book_one.status, Book.BORROWED)

    def test_borrow_limit_and_unpaid_fines_are_enforced(self):
        self.student_policy.max_books = 1
        self.student_policy.save()
        self.issue()
        with self.assertRaisesMessage(ValidationError, "Borrowing limit reached"):
            self.issue(book_copy=self.copy_two)

        Fine.objects.create(
            member=self.second_student,
            amount=Decimal("5.00"),
            reason=Fine.OTHER,
        )
        with self.assertRaisesMessage(ValidationError, "unpaid fines"):
            self.issue(member=self.second_student, book_copy=self.copy_two)

    def test_member_cannot_borrow_two_copies_of_same_title(self):
        self.issue()
        second_copy = BookCopy.objects.create(book=self.book_one, barcode="CIRC-COPY-004")
        with self.assertRaisesMessage(ValidationError, "active loan for this title"):
            self.issue(book_copy=second_copy)

    def test_late_return_uses_the_rate_captured_when_issued(self):
        today = timezone.localdate()
        loan = self.issue(
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=5),
        )
        self.student_policy.fine_per_day = Decimal("9.00")
        self.student_policy.save()

        returned = return_book(loan, self.librarian_user, return_date=today)
        loan.refresh_from_db()
        self.copy_one.refresh_from_db()
        fine = Fine.objects.get(borrow_record=loan, reason=Fine.LATE_RETURN)
        self.assertEqual(returned.fine_amount, Decimal("10.00"))
        self.assertEqual(fine.amount, Decimal("10.00"))
        self.assertEqual(loan.status, BorrowRecord.RETURNED)
        self.assertEqual(self.copy_one.status, BookCopy.AVAILABLE)

    def test_return_rejects_future_dates(self):
        loan = self.issue()
        with self.assertRaisesMessage(ValidationError, "cannot be in the future"):
            return_book(
                loan,
                self.librarian_user,
                return_date=timezone.localdate() + timedelta(days=1),
            )

    def test_damaged_return_updates_status_tracking(self):
        loan = self.issue()
        return_book(
            loan,
            self.librarian_user,
            book_condition=ReturnRecord.DAMAGED,
            remarks="Cover and binding damaged.",
        )
        loan.refresh_from_db()
        self.copy_one.refresh_from_db()
        self.assertEqual(loan.status, BorrowRecord.DAMAGED)
        self.assertEqual(self.copy_one.status, BookCopy.DAMAGED)
        self.assertTrue(DamagedBook.objects.filter(borrow_record=loan).exists())

    def test_renewal_extends_due_date_and_respects_limit(self):
        loan = self.issue()
        original_due_date = loan.due_date
        renewal = renew_borrow(loan, self.librarian_user, remarks="First renewal")
        loan.refresh_from_db()
        self.assertEqual(
            renewal.new_due_date,
            original_due_date + timedelta(days=self.student_policy.renewal_days),
        )
        self.assertEqual(loan.renewal_count, 1)
        self.assertEqual(RenewalRecord.objects.filter(borrow_record=loan).count(), 1)
        with self.assertRaisesMessage(ValidationError, "Renewal limit reached"):
            renew_borrow(loan, self.librarian_user)

    def test_another_members_reservation_blocks_renewal(self):
        loan = self.issue()
        reserve_book(self.second_student, self.book_one)
        with self.assertRaisesMessage(ValidationError, "another member reserved"):
            renew_borrow(loan, self.librarian_user)

    def test_reservation_requires_registered_unavailable_stock(self):
        empty_title = Book.objects.create(title="No Registered Stock", book_code="CIRC-EMPTY")
        with self.assertRaisesMessage(ValidationError, "no registered copies"):
            reserve_book(self.student, empty_title)
        with self.assertRaisesMessage(ValidationError, "available copy"):
            reserve_book(self.student, self.book_one)

    def test_member_cannot_reserve_a_title_they_are_borrowing(self):
        self.issue()
        with self.assertRaisesMessage(ValidationError, "active loan for this title"):
            reserve_book(self.student, self.book_one)

    def test_return_promotes_oldest_reservation_and_notifies_member(self):
        loan = self.issue()
        reservation = reserve_book(self.second_student, self.book_one)
        self.assertIsNone(reservation.expiry_date)

        return_book(loan, self.librarian_user)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.READY)
        self.assertEqual(reservation.ready_date, timezone.localdate())
        self.assertEqual(
            reservation.expiry_date,
            timezone.localdate() + timedelta(days=self.student_policy.reservation_expiry_days),
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.second_student,
                notification_type=Notification.RESERVATION,
            ).exists()
        )

    def test_cancelling_ready_reservation_promotes_next_member(self):
        loan = self.issue()
        first = reserve_book(self.second_student, self.book_one)
        second = reserve_book(self.teacher, self.book_one)
        return_book(loan, self.librarian_user)
        first.refresh_from_db()
        self.assertEqual(first.status, Reservation.READY)

        update_reservation_status(first, Reservation.CANCELLED, self.librarian_user)
        second.refresh_from_db()
        self.assertEqual(second.status, Reservation.READY)

    def test_expired_ready_reservation_promotes_next_member(self):
        today = timezone.localdate()
        BookCopy.objects.filter(pk=self.copy_one.pk).update(status=BookCopy.AVAILABLE)
        first = Reservation.objects.create(
            member=self.student,
            book=self.book_one,
            reserved_date=today - timedelta(days=4),
            status=Reservation.READY,
            ready_date=today - timedelta(days=3),
            expiry_date=today - timedelta(days=1),
        )
        second = Reservation.objects.create(member=self.second_student, book=self.book_one)
        self.assertEqual(mark_expired_reservations(), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, Reservation.EXPIRED)
        self.assertEqual(second.status, Reservation.READY)


class CirculationFormTests(CirculationTestDataMixin, TestCase):
    def test_member_reservation_form_is_scoped_to_own_account(self):
        self.issue(member=self.teacher, book_copy=self.copy_one)
        form = ReservationForm(actor=self.student_user)
        self.assertEqual(list(form.fields["member"].queryset), [self.student])
        self.assertIn(self.book_one, form.fields["book"].queryset)

    def test_reservation_form_excludes_titles_without_registered_copies(self):
        empty_title = Book.objects.create(title="Empty Catalog Record", book_code="CIRC-NONE")
        form = ReservationForm(actor=self.librarian_user)
        self.assertNotIn(empty_title, form.fields["book"].queryset)

    def test_return_form_rejects_future_date(self):
        loan = self.issue()
        form = ReturnBookForm(
            data={
                "borrow_record": loan.pk,
                "return_date": timezone.localdate() + timedelta(days=1),
                "book_condition": ReturnRecord.GOOD,
                "remarks": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("return_date", form.errors)


class CirculationViewTests(CirculationTestDataMixin, TestCase):
    def test_member_sees_only_personal_circulation_history(self):
        own_loan = self.issue()
        other_loan = self.issue(member=self.teacher, book_copy=self.copy_two)
        Reservation.objects.create(member=self.student, book=self.book_two)
        Reservation.objects.create(member=self.teacher, book=self.book_one)
        self.client.force_login(self.student_user)

        loan_response = self.client.get(reverse("circulation:borrow_list"))
        self.assertContains(loan_response, own_loan.book_copy.copy_code)
        self.assertNotContains(loan_response, other_loan.book_copy.copy_code)

        reservation_response = self.client.get(reverse("circulation:reservation_list"))
        self.assertContains(reservation_response, self.student.member_code)
        self.assertNotContains(reservation_response, self.teacher.member_code)

    def test_librarian_can_issue_and_return_book_through_views(self):
        self.client.force_login(self.librarian_user)
        issue_response = self.client.post(
            reverse("circulation:borrow_create"),
            {
                "member": self.student.pk,
                "book_copy": self.copy_one.pk,
                "borrow_date": timezone.localdate(),
                "due_date": "",
                "notes": "Issued at desk.",
            },
        )
        loan = BorrowRecord.objects.get(member=self.student, book_copy=self.copy_one)
        self.assertRedirects(
            issue_response,
            reverse("circulation:borrow_detail", kwargs={"pk": loan.pk}),
        )

        return_response = self.client.post(
            reverse("circulation:return_borrow", kwargs={"pk": loan.pk}),
            {
                "borrow_record": loan.pk,
                "return_date": timezone.localdate(),
                "book_condition": ReturnRecord.GOOD,
                "remarks": "Returned at desk.",
            },
        )
        self.assertRedirects(
            return_response,
            reverse("circulation:borrow_detail", kwargs={"pk": loan.pk}),
        )
        loan.refresh_from_db()
        self.assertEqual(loan.status, BorrowRecord.RETURNED)

    def test_student_cannot_access_issue_book_view(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("circulation:borrow_create"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:dashboard"))


class CirculationAPITests(CirculationTestDataMixin, APITestCase):
    def test_member_cannot_create_reservation_for_another_member(self):
        self.issue(member=self.teacher, book_copy=self.copy_one)
        self.client.force_authenticate(self.student_user)
        response = self.client.post(
            "/api/reservations/",
            {"member": self.second_student.pk, "book": self.book_one.pk, "notes": "No"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("member", response.data)

    def test_member_can_create_and_cancel_own_reservation(self):
        self.issue(member=self.teacher, book_copy=self.copy_one)
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/reservations/",
            {"member": self.student.pk, "book": self.book_one.pk, "notes": "API hold"},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        reservation = Reservation.objects.get(pk=create_response.data["id"])
        self.assertIsNone(reservation.expiry_date)

        ready_response = self.client.post(
            f"/api/reservations/{reservation.pk}/status/",
            {"status": Reservation.READY},
            format="json",
        )
        self.assertEqual(ready_response.status_code, 400)

        cancel_response = self.client.post(
            f"/api/reservations/{reservation.pk}/status/",
            {"status": Reservation.CANCELLED},
            format="json",
        )
        self.assertEqual(cancel_response.status_code, 200)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.CANCELLED)

    def test_circulation_transactions_cannot_be_patched_through_api(self):
        loan = self.issue()
        self.client.force_authenticate(self.superuser)
        response = self.client.patch(
            f"/api/borrow-records/{loan.pk}/",
            {"status": BorrowRecord.RETURNED},
            format="json",
        )
        self.assertEqual(response.status_code, 405)
        loan.refresh_from_db()
        self.assertEqual(loan.status, BorrowRecord.BORROWED)

    def test_member_api_list_is_scoped_to_personal_loans(self):
        own = self.issue()
        other = self.issue(member=self.teacher, book_copy=self.copy_two)
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/borrow-records/")
        self.assertEqual(response.status_code, 200)
        payload = response.data.get("results", response.data)
        identifiers = {item["id"] for item in payload}
        self.assertIn(own.pk, identifiers)
        self.assertNotIn(other.pk, identifiers)

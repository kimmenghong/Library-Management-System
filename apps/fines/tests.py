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
from apps.circulation.services import borrow_book
from apps.members.models import Member

from .forms import FineCreateForm, PaymentForm
from .models import Fine, Payment
from .services import (
    create_fine,
    record_payment,
    update_fine,
    void_payment,
    waive_fine,
)


User = get_user_model()


class FineTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.student_role = Role.objects.get(slug=Role.STUDENT)
        cls.teacher_role = Role.objects.get(slug=Role.TEACHER)
        cls.librarian_role = Role.objects.get(slug=Role.LIBRARIAN)

        cls.librarian = User.objects.create_user(
            username="fine_librarian",
            email="fine.librarian@example.com",
            password="StrongPass123!",
            first_name="Fine",
            last_name="Librarian",
            role=cls.librarian_role,
            is_staff=True,
        )
        cls.student_user = User.objects.create_user(
            username="fine_student",
            email="fine.student@example.com",
            password="StrongPass123!",
            first_name="Fine",
            last_name="Student",
            role=cls.student_role,
        )
        cls.teacher_user = User.objects.create_user(
            username="fine_teacher",
            email="fine.teacher@example.com",
            password="StrongPass123!",
            first_name="Fine",
            last_name="Teacher",
            role=cls.teacher_role,
        )
        cls.superuser = User.objects.create_superuser(
            username="fine_root",
            email="fine.root@example.com",
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

        cls.book = Book.objects.create(title="Financial Workflows", book_code="FINE-001")
        cls.copy = BookCopy.objects.create(book=cls.book, barcode="FINE-COPY-001")
        cls.other_book = Book.objects.create(title="Payment Ledgers", book_code="FINE-002")
        cls.other_copy = BookCopy.objects.create(
            book=cls.other_book,
            barcode="FINE-COPY-002",
        )

    def make_fine(self, member=None, amount="10.00", **kwargs):
        return create_fine(
            member=member or self.student,
            amount=Decimal(amount),
            reason=kwargs.pop("reason", Fine.OTHER),
            description=kwargs.pop("description", "Test assessment"),
            created_by=self.librarian,
            **kwargs,
        )

    def pay(self, fine, amount="2.00", **kwargs):
        return record_payment(
            fine=fine,
            amount_paid=Decimal(amount),
            payment_method=kwargs.pop("payment_method", Payment.CASH),
            payment_date=kwargs.pop("payment_date", timezone.localdate()),
            received_by=self.librarian,
            reference_number=kwargs.pop("reference_number", "TEST-REF"),
            notes=kwargs.pop("notes", "Test payment"),
            **kwargs,
        )


class FineModelTests(FineTestDataMixin, TestCase):
    def test_fine_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            Fine.objects.create(
                member=self.student,
                amount=Decimal("0.00"),
                reason=Fine.OTHER,
            )

    def test_fine_member_must_match_borrow_record(self):
        loan = borrow_book(self.student, self.copy, self.librarian)
        with self.assertRaisesMessage(ValidationError, "must match"):
            self.make_fine(
                member=self.teacher,
                borrow_record=loan,
                reason=Fine.LATE_RETURN,
            )

    def test_only_one_late_return_fine_is_allowed_per_loan(self):
        loan = borrow_book(self.student, self.copy, self.librarian)
        self.make_fine(borrow_record=loan, reason=Fine.LATE_RETURN)
        with self.assertRaises(ValidationError):
            self.make_fine(borrow_record=loan, reason=Fine.LATE_RETURN)

    def test_member_visibility_querysets_are_private(self):
        own = self.make_fine()
        other = self.make_fine(member=self.teacher)
        visible = Fine.objects.visible_to(self.student_user)
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)


class PaymentAccountingTests(FineTestDataMixin, TestCase):
    def test_partial_and_full_payments_recalculate_fine(self):
        fine = self.make_fine(amount="10.00")
        first = self.pay(fine, "4.00")
        fine.refresh_from_db()
        self.assertEqual(first.member, self.student)
        self.assertEqual(fine.paid_amount, Decimal("4.00"))
        self.assertEqual(fine.balance, Decimal("6.00"))
        self.assertEqual(fine.status, Fine.PARTIAL)

        self.pay(fine, "6.00")
        fine.refresh_from_db()
        self.assertEqual(fine.paid_amount, Decimal("10.00"))
        self.assertEqual(fine.balance, Decimal("0.00"))
        self.assertEqual(fine.status, Fine.PAID)

    def test_overpayment_is_rejected_without_creating_history(self):
        fine = self.make_fine(amount="5.00")
        with self.assertRaisesMessage(ValidationError, "cannot exceed"):
            self.pay(fine, "5.01")
        fine.refresh_from_db()
        self.assertEqual(fine.paid_amount, Decimal("0.00"))
        self.assertFalse(fine.payments.exists())

    def test_future_payment_date_is_rejected(self):
        fine = self.make_fine()
        with self.assertRaisesMessage(ValidationError, "cannot be in the future"):
            self.pay(
                fine,
                payment_date=timezone.localdate() + timedelta(days=1),
            )

    def test_completed_payment_details_are_immutable_and_not_deletable(self):
        fine = self.make_fine()
        payment = self.pay(fine)
        payment.reference_number = "CHANGED"
        with self.assertRaisesMessage(ValidationError, "immutable"):
            payment.save()
        payment.refresh_from_db()
        with self.assertRaisesMessage(ValidationError, "cannot be deleted"):
            payment.delete()

    def test_voiding_payment_restores_outstanding_balance(self):
        fine = self.make_fine(amount="10.00")
        payment = self.pay(fine, "10.00")
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.PAID)

        void_payment(
            payment=payment,
            voided_by=self.librarian,
            reason="Duplicate receipt entered at desk.",
        )
        payment.refresh_from_db()
        fine.refresh_from_db()
        self.assertEqual(payment.status, Payment.VOIDED)
        self.assertEqual(payment.effective_amount, Decimal("0.00"))
        self.assertEqual(fine.status, Fine.UNPAID)
        self.assertEqual(fine.paid_amount, Decimal("0.00"))
        self.assertEqual(fine.balance, Decimal("10.00"))

    def test_waiver_closes_remaining_partial_balance(self):
        fine = self.make_fine(amount="10.00")
        self.pay(fine, "3.00")
        waive_fine(
            fine=fine,
            waived_by=self.librarian,
            reason="Approved hardship waiver.",
        )
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.WAIVED)
        self.assertEqual(fine.paid_amount, Decimal("3.00"))
        self.assertEqual(fine.balance, Decimal("0.00"))
        self.assertEqual(fine.waived_by, self.librarian)
        with self.assertRaisesMessage(ValidationError, "outstanding fines"):
            self.pay(fine)

    def test_fine_with_payment_history_cannot_be_edited(self):
        fine = self.make_fine()
        self.pay(fine)
        with self.assertRaisesMessage(ValidationError, "payment history"):
            update_fine(
                fine=fine,
                amount=Decimal("12.00"),
                reason=Fine.OTHER,
                description="Changed",
                updated_by=self.librarian,
            )


class FineFormTests(FineTestDataMixin, TestCase):
    def test_late_return_form_requires_borrow_record(self):
        form = FineCreateForm(
            data={
                "borrow_record": "",
                "member": self.student.pk,
                "amount": "3.00",
                "reason": Fine.LATE_RETURN,
                "description": "Late",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("borrow_record", form.errors)

    def test_payment_form_rejects_more_than_balance(self):
        fine = self.make_fine(amount="4.00")
        form = PaymentForm(
            data={
                "fine": fine.pk,
                "amount_paid": "5.00",
                "payment_method": Payment.CASH,
                "payment_date": timezone.localdate(),
                "reference_number": "",
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("amount_paid", form.errors)


class FineViewTests(FineTestDataMixin, TestCase):
    def test_member_sees_only_personal_fines_and_payments(self):
        own_fine = self.make_fine()
        other_fine = self.make_fine(member=self.teacher)
        own_payment = self.pay(own_fine)
        other_payment = self.pay(other_fine)
        self.client.force_login(self.student_user)

        fine_response = self.client.get(reverse("fines:fine_list"))
        self.assertEqual(fine_response.status_code, 200)
        self.assertContains(
            fine_response,
            reverse("fines:fine_detail", kwargs={"pk": own_fine.pk}),
        )
        self.assertNotContains(fine_response, self.teacher.member_code)
        other_detail = self.client.get(reverse("fines:fine_detail", kwargs={"pk": other_fine.pk}))
        self.assertEqual(other_detail.status_code, 404)

        payment_response = self.client.get(reverse("fines:payment_list"))
        self.assertEqual(payment_response.status_code, 200)
        self.assertContains(payment_response, reverse("fines:payment_detail", kwargs={"pk": own_payment.pk}))
        self.assertNotContains(payment_response, reverse("fines:payment_detail", kwargs={"pk": other_payment.pk}))

    def test_librarian_can_create_fine_and_record_payment(self):
        self.client.force_login(self.librarian)
        create_response = self.client.post(
            reverse("fines:fine_create"),
            {
                "borrow_record": "",
                "member": self.student.pk,
                "amount": "8.00",
                "reason": Fine.OTHER,
                "description": "Replacement card charge",
            },
        )
        fine = Fine.objects.get(description="Replacement card charge")
        self.assertRedirects(
            create_response,
            reverse("fines:fine_detail", kwargs={"pk": fine.pk}),
        )

        payment_response = self.client.post(
            reverse("fines:payment_create_for_fine", kwargs={"fine_pk": fine.pk}),
            {
                "fine_context": fine.pk,
                "fine": fine.pk,
                "amount_paid": "3.00",
                "payment_method": Payment.CASH,
                "payment_date": timezone.localdate(),
                "reference_number": "DESK-001",
                "notes": "Cash received",
            },
        )
        payment = Payment.objects.get(fine=fine)
        self.assertRedirects(
            payment_response,
            reverse("fines:payment_detail", kwargs={"pk": payment.pk}),
        )
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.PARTIAL)

    def test_student_cannot_open_financial_management_forms(self):
        fine = self.make_fine()
        self.client.force_login(self.student_user)
        for url in (
            reverse("fines:fine_create"),
            reverse("fines:fine_update", kwargs={"pk": fine.pk}),
            reverse("fines:fine_waive", kwargs={"pk": fine.pk}),
            reverse("fines:payment_create_for_fine", kwargs={"fine_pk": fine.pk}),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("accounts:dashboard"))


class FineAPITests(FineTestDataMixin, APITestCase):
    def test_member_api_lists_are_scoped_to_personal_history(self):
        own_fine = self.make_fine()
        other_fine = self.make_fine(member=self.teacher)
        own_payment = self.pay(own_fine)
        other_payment = self.pay(other_fine)
        self.client.force_authenticate(self.student_user)

        fine_response = self.client.get("/api/fines/")
        fine_payload = fine_response.data.get("results", fine_response.data)
        self.assertEqual({item["id"] for item in fine_payload}, {own_fine.pk})

        payment_response = self.client.get("/api/payments/")
        payment_payload = payment_response.data.get("results", payment_response.data)
        self.assertEqual({item["id"] for item in payment_payload}, {own_payment.pk})
        self.assertNotIn(other_payment.pk, {item["id"] for item in payment_payload})

    def test_api_uses_payment_and_waiver_workflows(self):
        self.client.force_authenticate(self.librarian)
        fine_response = self.client.post(
            "/api/fines/",
            {
                "member": self.student.pk,
                "amount": "12.00",
                "reason": Fine.OTHER,
                "description": "API assessment",
            },
            format="json",
        )
        self.assertEqual(fine_response.status_code, 201, fine_response.data)
        fine = Fine.objects.get(pk=fine_response.data["id"])

        payment_response = self.client.post(
            "/api/payments/",
            {
                "fine": fine.pk,
                "amount_paid": "4.00",
                "payment_method": Payment.CARD,
                "payment_date": timezone.localdate(),
                "reference_number": "API-001",
            },
            format="json",
        )
        self.assertEqual(payment_response.status_code, 201, payment_response.data)
        payment = Payment.objects.get(pk=payment_response.data["id"])

        waive_response = self.client.post(
            f"/api/fines/{fine.pk}/waive/",
            {"reason": "Approved API waiver."},
            format="json",
        )
        self.assertEqual(waive_response.status_code, 200)
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.WAIVED)

        void_response = self.client.post(
            f"/api/payments/{payment.pk}/void/",
            {"reason": "API payment reversal."},
            format="json",
        )
        self.assertEqual(void_response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.VOIDED)

    def test_api_rejects_overpayment_and_transaction_patch(self):
        fine = self.make_fine(amount="5.00")
        self.client.force_authenticate(self.librarian)
        overpayment = self.client.post(
            "/api/payments/",
            {
                "fine": fine.pk,
                "amount_paid": "6.00",
                "payment_method": Payment.CASH,
                "payment_date": timezone.localdate(),
            },
            format="json",
        )
        self.assertEqual(overpayment.status_code, 400)
        self.assertFalse(Payment.objects.filter(fine=fine).exists())

        patch_response = self.client.patch(
            f"/api/fines/{fine.pk}/",
            {"status": Fine.PAID},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 405)

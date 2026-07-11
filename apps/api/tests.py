from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Permission, Role
from apps.catalog.models import Book, BookCopy
from apps.circulation.models import BorrowRecord, Reservation
from apps.circulation.services import borrow_book, reserve_book, return_book
from apps.fines.models import Fine
from apps.members.models import Member


User = get_user_model()


def ensure_permission(codename, module="catalog", action="view"):
    permission, _ = Permission.objects.get_or_create(
        codename=codename,
        defaults={
            "name": codename,
            "module": module,
            "action": action,
            "is_active": True,
        },
    )
    return permission


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_jwt_user",
            email="api_jwt_user@example.com",
            password="Passw0rd!123",
        )

    def test_jwt_login_and_refresh(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "api_jwt_user", "password": "Passw0rd!123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "api_jwt_user")

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)


class APIRolePermissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_reader",
            email="api_reader@example.com",
            password="Passw0rd!123",
        )
        self.role = Role.objects.create(name="API Reader", slug="api-reader")
        self.book = Book.objects.create(title="API Permission Book", book_code="API-PERM-001")

    def test_book_api_requires_role_permission(self):
        self.client.force_authenticate(self.user)
        denied = self.client.get("/api/books/")
        self.assertEqual(denied.status_code, 403)

        self.role.permissions.add(ensure_permission("catalog.view_book"))
        self.user.role = self.role
        self.user.save(update_fields=["role"])

        allowed = self.client.get("/api/books/")
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("results", allowed.data)


class APICirculationIntegrationTests(APITestCase):
    def setUp(self):
        create_borrow = ensure_permission("circulation.create_borrow", "circulation", "add")
        view_borrow = ensure_permission("circulation.view_borrow", "circulation", "view")
        self.librarian_role = Role.objects.create(name="API Librarian", slug="api-librarian")
        self.librarian_role.permissions.add(create_borrow, view_borrow)
        self.librarian = User.objects.create_user(
            username="api_librarian",
            email="api_librarian@example.com",
            password="Passw0rd!123",
            role=self.librarian_role,
        )
        self.member_user = User.objects.create_user(
            username="api_member",
            email="api_member@example.com",
            password="Passw0rd!123",
        )
        self.member = Member.objects.create(user=self.member_user, member_type=Member.STUDENT)
        self.book = Book.objects.create(title="API Borrow Book", book_code="API-BORROW-001")
        self.copy = BookCopy.objects.create(book=self.book, copy_code="API-BORROW-C001")

    def test_borrow_record_api_updates_copy_status(self):
        self.client.force_authenticate(self.librarian)
        response = self.client.post(
            "/api/borrow-records/",
            {
                "member": self.member.id,
                "book_copy": self.copy.id,
                "borrow_date": timezone.localdate(),
                "due_date": timezone.localdate() + timedelta(days=7),
                "notes": "API integration test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.BORROWED)


class APIFileUploadSecurityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="api_admin",
            email="api_admin@example.com",
            password="Passw0rd!123",
        )

    def test_digital_book_rejects_unsafe_extension(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/digital-books/",
            {
                "title": "Unsafe Upload",
                "is_public": True,
                "file": SimpleUploadedFile("unsafe.exe", b"not allowed", content_type="application/octet-stream"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)


class FinalProjectIntegrationTests(TestCase):
    def setUp(self):
        self.password = "Password@123"
        self.dashboard_permission = ensure_permission("dashboard.view_dashboard", "dashboard", "view")
        self.report_view_permission = ensure_permission("reports.view_report", "reports", "view")
        self.report_export_permission = ensure_permission("reports.export_report", "reports", "export")

    def make_role(self, slug, *permissions):
        role, _ = Role.objects.get_or_create(slug=slug, defaults={"name": slug.replace("_", " ").title()})
        role.permissions.add(*permissions)
        return role

    def make_user(self, username, role):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=self.password,
            role=role,
            is_active=True,
        )

    def test_login_by_required_roles(self):
        roles = [
            Role.SUPER_ADMIN,
            Role.ADMIN,
            Role.LIBRARIAN,
            Role.ASSISTANT_LIBRARIAN,
            Role.STUDENT,
            Role.TEACHER,
            Role.STAFF,
            Role.GUEST,
        ]
        client = Client()
        for slug in roles:
            role = self.make_role(slug, self.dashboard_permission)
            self.make_user(f"login_{slug}", role)
            response = client.post("/login/", {"username": f"login_{slug}", "password": self.password})
            self.assertEqual(response.status_code, 302, slug)
            client.post("/logout/")

    def test_borrow_return_and_fine_calculation_flow(self):
        librarian_role = self.make_role(Role.LIBRARIAN)
        librarian = self.make_user("flow_librarian", librarian_role)
        member_user = self.make_user("flow_student", self.make_role(Role.STUDENT))
        member = Member.objects.create(user=member_user, member_type=Member.STUDENT)
        book = Book.objects.create(title="Fine Flow Book", book_code="FLOW-FINE-001")
        copy = BookCopy.objects.create(book=book, copy_code="FLOW-FINE-C001")
        today = timezone.localdate()

        borrow = borrow_book(
            member,
            copy,
            librarian,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=3),
        )
        return_record = return_book(borrow, librarian, return_date=today)

        copy.refresh_from_db()
        borrow.refresh_from_db()
        fine = Fine.objects.get(borrow_record=borrow)
        self.assertEqual(copy.status, BookCopy.AVAILABLE)
        self.assertEqual(borrow.status, BorrowRecord.RETURNED)
        self.assertEqual(return_record.fine_amount, fine.amount)
        self.assertEqual(fine.amount, fine.member.fines.first().amount)
        self.assertGreater(fine.amount, 0)

    def test_reservation_flow_requires_unavailable_book(self):
        librarian = self.make_user("reservation_librarian", self.make_role(Role.LIBRARIAN))
        teacher_user = self.make_user("reservation_teacher", self.make_role(Role.TEACHER))
        student_user = self.make_user("reservation_student", self.make_role(Role.STUDENT))
        teacher = Member.objects.create(user=teacher_user, member_type=Member.TEACHER)
        student = Member.objects.create(user=student_user, member_type=Member.STUDENT)
        book = Book.objects.create(title="Reservation Flow Book", book_code="FLOW-RES-001")
        copy = BookCopy.objects.create(book=book, copy_code="FLOW-RES-C001")

        borrow_book(teacher, copy, librarian)
        reservation = reserve_book(student, book, notes="Integration reservation")

        self.assertEqual(reservation.status, Reservation.PENDING)
        self.assertEqual(reservation.book, book)
        self.assertEqual(reservation.member, student)

    def test_report_export_works_for_authorized_user(self):
        role = self.make_role(Role.LIBRARIAN, self.report_view_permission, self.report_export_permission)
        user = self.make_user("report_librarian", role)
        book = Book.objects.create(title="Report Flow Book", book_code="FLOW-REPORT-001")
        copy = BookCopy.objects.create(book=book, copy_code="FLOW-REPORT-C001")
        member_user = self.make_user("report_student", self.make_role(Role.STUDENT))
        member = Member.objects.create(user=member_user, member_type=Member.STUDENT)
        borrow_book(member, copy, user)

        client = Client()
        client.force_login(user)
        response = client.get("/reports/export/most-borrowed/excel/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheet", response["Content-Type"])

    def test_admin_and_sample_data_commands(self):
        call_command("setup_admin", username="command_admin", email="command_admin@example.com", password="Admin@12345", verbosity=0)
        self.assertTrue(User.objects.filter(username="command_admin", is_superuser=True).exists())

        call_command("seed_sample_data", verbosity=0)
        self.assertTrue(Book.objects.filter(book_code="LMS-CLEAN-CODE").exists())
        self.assertTrue(Member.objects.filter(user__username="sample_student").exists())
        self.assertTrue(Reservation.objects.filter(notes__icontains="Sample reservation").exists())

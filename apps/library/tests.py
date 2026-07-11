import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Author,
    Book,
    BorrowRecord,
    Category,
    Fine,
    Member,
    Notification,
    Publisher,
    Report,
    Role,
    User,
)
from .services.supabase_auth import SupabaseAuthIdentity, SupabaseAuthService
from .views import LocalUserSyncError, _validate_local_login_user


class LibraryTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.student_role = Role.objects.create(role_name="Student")
        cls.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
            full_name="Library Admin",
            role=cls.admin_role,
            is_staff=True,
        )
        cls.member_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="StrongPass123!",
            full_name="Student Member",
            role=cls.student_role,
        )
        cls.category = Category.objects.create(category_name="Computing")
        cls.author = Author.objects.create(author_name="Test Author")
        cls.publisher = Publisher.objects.create(publisher_name="Test Publisher")
        cls.book = Book.objects.create(
            category=cls.category,
            author=cls.author,
            publisher=cls.publisher,
            isbn="9780132350884",
            title="Clean Code",
            publication_year=2008,
            quantity=2,
            available_quantity=2,
        )
        cls.member = Member.objects.create(
            user=cls.member_user,
            member_code="STU001",
            member_type=Member.STUDENT,
            department="Computer Science",
        )


class DataDictionaryModelTests(LibraryTestDataMixin, TestCase):
    def test_required_table_and_primary_key_names(self):
        expected = {
            Role: ("roles", "role_id"),
            User: ("users", "user_id"),
            Category: ("categories", "category_id"),
            Author: ("authors", "author_id"),
            Publisher: ("publishers", "publisher_id"),
            Book: ("books", "book_id"),
            Member: ("members", "member_id"),
            BorrowRecord: ("borrow_records", "borrow_id"),
            Fine: ("fines", "fine_id"),
            Notification: ("notifications", "notification_id"),
            Report: ("reports", "report_id"),
        }
        for model, (table_name, primary_key) in expected.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(model._meta.db_table, table_name)
                self.assertEqual(model._meta.pk.name, primary_key)

    def test_borrow_record_uses_book_and_processing_users(self):
        field_names = {field.name for field in BorrowRecord._meta.fields}
        self.assertIn("book", field_names)
        self.assertNotIn("book_copy", field_names)
        self.assertIs(BorrowRecord._meta.get_field("book").remote_field.model, Book)
        self.assertIs(
            BorrowRecord._meta.get_field("issued_by").remote_field.model,
            User,
        )
        self.assertIs(
            BorrowRecord._meta.get_field("received_by").remote_field.model,
            User,
        )

    def test_notification_and_report_relationships(self):
        self.assertIs(
            Notification._meta.get_field("member").remote_field.model,
            Member,
        )
        self.assertIs(
            Report._meta.get_field("generated_by").remote_field.model,
            User,
        )

    def test_all_eleven_tables_accept_valid_records(self):
        today = timezone.localdate()
        borrow = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today,
            due_date=today + timedelta(days=14),
        )
        fine = Fine.objects.create(
            borrow=borrow,
            member=self.member,
            amount=Decimal("2.00"),
        )
        notification = Notification.objects.create(
            member=self.member,
            title="Test notification",
            message="This notification belongs to a member.",
        )
        report = Report.objects.create(
            report_type=Report.BOOKS,
            generated_by=self.admin_user,
        )

        records = [
            self.admin_role,
            self.admin_user,
            self.category,
            self.author,
            self.publisher,
            self.book,
            self.member,
            borrow,
            fine,
            notification,
            report,
        ]
        self.assertTrue(all(record.pk is not None for record in records))


class BorrowingWorkflowTests(LibraryTestDataMixin, TestCase):
    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_issue_book_decrements_book_availability(self):
        response = self.client.post(
            reverse("library:borrow_create"),
            {
                "member": self.member.member_id,
                "book": self.book.book_id,
                "borrow_date": timezone.localdate(),
                "due_date": timezone.localdate() + timedelta(days=14),
            },
        )

        self.assertRedirects(response, reverse("library:borrow_list"))
        record = BorrowRecord.objects.get()
        self.book.refresh_from_db()
        self.assertEqual(record.book, self.book)
        self.assertEqual(record.issued_by, self.admin_user)
        self.assertIsNone(record.received_by)
        self.assertEqual(self.book.available_quantity, 1)

    def test_late_return_records_receiver_fine_and_notification(self):
        today = timezone.localdate()
        self.book.available_quantity = 1
        self.book.save()
        record = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=5),
        )

        response = self.client.post(
            reverse("library:borrow_return", args=[record.borrow_id]),
            {"return_date": today},
        )

        self.assertRedirects(response, reverse("library:borrow_list"))
        record.refresh_from_db()
        self.book.refresh_from_db()
        fine = Fine.objects.get(borrow=record)
        notification = Notification.objects.get(member=self.member)
        self.assertEqual(record.status, BorrowRecord.RETURNED)
        self.assertEqual(record.received_by, self.admin_user)
        self.assertEqual(record.return_date, today)
        self.assertEqual(self.book.available_quantity, 2)
        self.assertEqual(fine.amount, Decimal("5.00"))
        self.assertEqual(notification.notification_type, Notification.FINE)


class AccessAndNotificationTests(LibraryTestDataMixin, TestCase):
    def test_staff_pages_render_with_corrected_schema(self):
        self.client.force_login(self.admin_user)
        urls = [
            reverse("library:dashboard"),
            reverse("library:book_list"),
            reverse("library:borrow_list"),
            reverse("library:fine_list"),
            reverse("library:notification_list"),
            reverse("library:report_list"),
        ]
        urls.extend(
            reverse("library:entity_list", kwargs={"entity": entity})
            for entity in [
                "roles",
                "users",
                "categories",
                "authors",
                "publishers",
                "members",
            ]
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_member_sees_only_their_notifications(self):
        Notification.objects.create(
            member=self.member,
            title="Due date reminder",
            message="Your book is due soon.",
            notification_type=Notification.DUE_DATE,
        )
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPass123!",
            full_name="Other Member",
            role=self.student_role,
        )
        other_member = Member.objects.create(
            user=other_user,
            member_code="STU002",
            member_type=Member.STUDENT,
        )
        Notification.objects.create(
            member=other_member,
            title="Other notice",
            message="Not visible to the first member.",
        )
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("library:notification_list"))

        self.assertContains(response, "Due date reminder")
        self.assertNotContains(response, "Other notice")


class SupabaseAuthViewTests(LibraryTestDataMixin, TestCase):
    @override_settings(USE_SUPABASE_AUTH=False)
    def test_auth_pages_render_without_changing_schema(self):
        for url_name in ["login", "register"]:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(f"library:{url_name}"))
                self.assertEqual(response.status_code, 200)

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_local_fallback_login_accepts_email_when_supabase_disabled(self):
        response = self.client.post(
            reverse("library:login"),
            {"email": "admin@example.com", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("library:dashboard"))

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_inactive_local_user_is_blocked_from_fallback_login(self):
        self.admin_user.is_active = False
        self.admin_user.save(update_fields=["is_active", "updated_at"])

        response = self.client.post(
            reverse("library:login"),
            {"email": "admin@example.com", "password": "StrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inactive")


class SupabaseAuthIntegrationTests(LibraryTestDataMixin, TestCase):
    def _identity(self, email, *, user_id="supabase-user-id", has_session=True):
        return SupabaseAuthIdentity(
            supabase_user_id=user_id,
            email=email,
            access_token="access-token" if has_session else "",
            refresh_token="refresh-token" if has_session else "",
            raw={"user": {"id": user_id, "email": email}},
        )

    @override_settings(
        USE_SUPABASE_AUTH=True,
        SUPABASE_URL="https://aeqcvoglxjlefbkurrys.supabase.co",
        SUPABASE_ANON_KEY="test-anon-key",
        SUPABASE_AUTH_TIMEOUT=5,
    )
    def test_supabase_service_connection_uses_auth_endpoint(self):
        response = Mock(status_code=200, content=b"{}")
        response.json.return_value = {
            "user": {
                "id": "supabase-user-id",
                "email": "admin@example.com",
            },
            "session": {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
            },
        }
        http_client = Mock()
        http_client.request.return_value = response
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=http_client)
        context_manager.__exit__ = Mock(return_value=False)

        with patch(
            "apps.library.services.supabase_auth.httpx.Client",
            return_value=context_manager,
        ):
            identity = SupabaseAuthService().sign_in_with_password(
                email="admin@example.com",
                password="StrongPass123!",
            )

        request_args, request_kwargs = http_client.request.call_args
        self.assertEqual(request_args[0], "POST")
        self.assertIn("/auth/v1/token", request_args[1])
        self.assertEqual(request_kwargs["params"]["grant_type"], "password")
        self.assertEqual(request_kwargs["headers"]["apikey"], "test-anon-key")
        self.assertEqual(identity.email, "admin@example.com")
        self.assertTrue(identity.has_session)

    @override_settings(
        USE_SUPABASE_AUTH=True,
        SUPABASE_AUTH_REQUIRE_LOCAL_USER=True,
        SUPABASE_AUTH_SESSION_KEY="supabase_auth",
    )
    def test_login_with_supabase_auth_syncs_to_existing_django_user(self):
        service = Mock()
        service.sign_in_with_password.return_value = self._identity(
            self.admin_user.email
        )

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(
                reverse("library:login"),
                {"email": self.admin_user.email, "password": "StrongPass123!"},
            )

        self.assertRedirects(response, reverse("library:dashboard"))
        service.sign_in_with_password.assert_called_once_with(
            email=self.admin_user.email,
            password="StrongPass123!",
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin_user.pk)
        self.assertEqual(
            self.client.session["supabase_auth"]["email"],
            self.admin_user.email,
        )

    @override_settings(
        USE_SUPABASE_AUTH=True,
        SUPABASE_AUTH_DEFAULT_ROLE="Student",
        SUPABASE_AUTH_SESSION_KEY="supabase_auth",
    )
    def test_register_with_supabase_auth_creates_local_django_user(self):
        email = "new.member@example.com"
        service = Mock()
        service.sign_up.return_value = self._identity(email)

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(
                reverse("library:register"),
                {
                    "full_name": "New Library Member",
                    "email": email,
                    "phone": "012345678",
                    "address": "University Campus",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
            )

        self.assertRedirects(response, reverse("library:dashboard"))
        user = User.objects.select_related("role").get(email=email)
        self.assertEqual(user.full_name, "New Library Member")
        self.assertEqual(user.role.role_name, "Student")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    @override_settings(
        USE_SUPABASE_AUTH=True, SUPABASE_AUTH_SESSION_KEY="supabase_auth"
    )
    def test_logout_clears_django_and_supabase_sessions(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session["supabase_auth"] = {
            "user_id": "supabase-user-id",
            "email": self.admin_user.email,
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        }
        session.save()
        service = Mock()

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(reverse("library:logout"))

        self.assertRedirects(response, reverse("library:login"))
        service.sign_out.assert_called_once_with(access_token="access-token")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("supabase_auth", self.client.session)

    @override_settings(USE_SUPABASE_AUTH=True)
    def test_inactive_user_cannot_login_with_supabase_auth(self):
        self.admin_user.is_active = False
        self.admin_user.save(update_fields=["is_active", "updated_at"])
        service = Mock()
        service.sign_in_with_password.return_value = self._identity(
            self.admin_user.email
        )

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(
                reverse("library:login"),
                {"email": self.admin_user.email, "password": "StrongPass123!"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inactive")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_user_without_role_is_blocked_by_local_validation(self):
        user = User(
            username="no_role",
            email="no_role@example.com",
            full_name="No Role",
            is_active=True,
        )

        with self.assertRaisesMessage(LocalUserSyncError, "no role assigned"):
            _validate_local_login_user(user)

    @override_settings(USE_SUPABASE_AUTH=True)
    def test_role_based_access_control_after_supabase_login(self):
        service = Mock()
        service.sign_in_with_password.return_value = self._identity(
            self.member_user.email
        )

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(
                reverse("library:login"),
                {"email": self.member_user.email, "password": "StrongPass123!"},
            )

        self.assertRedirects(response, reverse("library:dashboard"))
        self.assertEqual(self.client.get(reverse("library:book_list")).status_code, 200)
        staff_response = self.client.get(
            reverse("library:entity_list", kwargs={"entity": "users"})
        )
        self.assertEqual(staff_response.status_code, 302)
        self.assertIn("/login/", staff_response["Location"])

    def test_non_staff_cannot_open_master_data(self):
        self.client.force_login(self.member_user)
        response = self.client.get(
            reverse("library:entity_list", kwargs={"entity": "roles"})
        )
        self.assertEqual(response.status_code, 302)


class ReportTests(LibraryTestDataMixin, TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.client.force_login(self.admin_user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_report_generation_records_user_and_file(self):
        response = self.client.post(
            reverse("library:report_create"),
            {"report_type": Report.BOOKS},
        )

        self.assertRedirects(response, reverse("library:report_list"))
        report = Report.objects.get()
        self.assertEqual(report.generated_by, self.admin_user)
        self.assertTrue(report.file_path.name.endswith(".csv"))
        self.assertTrue(report.file_path.storage.exists(report.file_path.name))


class SeedDataCommandTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_seed_data_creates_valid_rows_in_all_required_tables(self):
        call_command("seed_data", verbosity=0)

        models = [
            Role,
            User,
            Category,
            Author,
            Publisher,
            Book,
            Member,
            BorrowRecord,
            Fine,
            Notification,
            Report,
        ]
        for model in models:
            with self.subTest(model=model.__name__):
                self.assertTrue(model.objects.exists())

        borrow = BorrowRecord.objects.get(
            member__member_code="STU-2026-001",
            book__isbn="9780132350884",
        )
        self.assertEqual(borrow.issued_by.username, "sample_librarian")
        self.assertIsNone(borrow.received_by)

        fine = Fine.objects.get(member__member_code="TCH-2026-001")
        self.assertEqual(fine.borrow.member, fine.member)
        self.assertEqual(fine.balance, Decimal("2.00"))
        self.assertTrue(Notification.objects.filter(member__isnull=False).exists())

        report = Report.objects.get(report_type=Report.BOOKS)
        self.assertEqual(report.generated_by.username, "sample_admin")
        self.assertTrue(report.file_path.storage.exists(report.file_path.name))

    def test_seed_data_is_repeatable(self):
        call_command("seed_data", verbosity=0)
        first_counts = {
            model: model.objects.count()
            for model in [
                Role,
                User,
                Category,
                Author,
                Publisher,
                Book,
                Member,
                BorrowRecord,
                Fine,
                Notification,
                Report,
            ]
        }

        call_command("seed_data", verbosity=0)

        for model, count in first_counts.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.count(), count)

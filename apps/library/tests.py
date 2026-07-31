import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import SimpleUploadedFile
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
from .views import (
    PUBLIC_CATALOG_BOOKS,
    PUBLIC_CATALOG_BY_ISBN,
    PUBLIC_CATALOG_PAGE_SIZE,
    LocalUserSyncError,
    _validate_local_login_user,
)


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


class PublicCatalogTests(TestCase):
    def _card_count(self, response):
        return response.content.decode().count("data-public-book-card")

    def _detail_url(self, book_code="BK-2001"):
        return reverse("library:public_book_detail", args=[book_code])

    def _code_for_title(self, title):
        return next(
            book["code"] for book in PUBLIC_CATALOG_BOOKS if book["title"] == title
        )

    def test_public_catalog_data_is_unique_and_complete(self):
        isbns = [book["isbn"] for book in PUBLIC_CATALOG_BOOKS]
        codes = [book["code"] for book in PUBLIC_CATALOG_BOOKS]
        missing_covers = [
            book["cover"]
            for book in PUBLIC_CATALOG_BOOKS
            if finders.find(book["cover"]) is None
        ]

        self.assertGreaterEqual(len(PUBLIC_CATALOG_BOOKS), 40)
        self.assertEqual(len(isbns), len(set(isbns)))
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(missing_covers, [])
        self.assertEqual(
            sum(1 for book in PUBLIC_CATALOG_BOOKS if "Harry Potter" in book["title"]),
            7,
        )
        required_titles = {
            "Harry Potter and the Chamber of Secrets",
            "Harry Potter and the Deathly Hallows",
            "The Lord of the Rings",
            "The Midnight Library",
            "Ikigai: The Japanese Secret to a Long and Happy Life",
            "The Silent Patient",
            "The Hobbit",
            "Atomic Habits",
            "Clean Code",
            "The Alchemist",
            "The Psychology of Money",
            "Introduction to Algorithms",
            "Design Patterns",
            "Computer Networking",
            "Operating System Concepts",
            "Database System Concepts",
            "Artificial Intelligence: A Modern Approach",
            "Clean Architecture",
            "Head First Java",
            "Python Crash Course",
            "Effective Java",
            "Diary of a Wimpy Kid",
            "To Kill a Mockingbird",
            "Pride and Prejudice",
            "The Adventures of Sherlock Holmes",
            "It",
            "Macbeth",
            "Me Before You",
            "The Hunger Games",
            "The Diary of a Young Girl",
            "Wonder",
        }
        catalog_titles = {book["title"] for book in PUBLIC_CATALOG_BOOKS}
        self.assertTrue(required_titles.issubset(catalog_titles))

    def test_requested_public_catalog_books_have_exact_metadata(self):
        expected = {
            "The Midnight Library": {
                "author": "Matt Haig",
                "category": "Fiction",
                "isbn": "9780525559474",
                "code": "BK-2051",
                "year": 2020,
                "edition": "First Edition",
                "publisher": "Canongate Books",
                "shelf_location": "FIC-A-01",
                "total_copies": 15,
                "available_copies": 12,
                "status": "Available",
                "cover": "images/books/the_midnight_library.jpg",
            },
            "Ikigai: The Japanese Secret to a Long and Happy Life": {
                "author": "Héctor García and Francesc Miralles",
                "category": "Self-Help",
                "isbn": "9780143130727",
                "code": "BK-2052",
                "year": 2017,
                "edition": "First Edition",
                "publisher": "Penguin Books",
                "shelf_location": "SEL-B-02",
                "total_copies": 10,
                "available_copies": 8,
                "status": "Available",
                "cover": "images/books/ikigai.jpg",
            },
            "The Silent Patient": {
                "author": "Alex Michaelides",
                "category": "Mystery & Thriller",
                "isbn": "9781250301697",
                "code": "BK-2053",
                "year": 2019,
                "edition": "First Edition",
                "publisher": "Celadon Books",
                "shelf_location": "MYS-C-03",
                "total_copies": 12,
                "available_copies": 5,
                "status": "Borrowed",
                "cover": "images/books/the_silent_patient.jpg",
            },
        }
        catalog_by_title = {book["title"]: book for book in PUBLIC_CATALOG_BOOKS}

        for title, fields in expected.items():
            with self.subTest(title=title):
                book = catalog_by_title[title]
                for key, value in fields.items():
                    self.assertEqual(book[key], value)
                self.assertIsNotNone(finders.find(book["cover"]))

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_first_page_renders_twelve_books(self):
        response = self.client.get(reverse("library:login"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._card_count(response), PUBLIC_CATALOG_PAGE_SIZE)
        self.assertEqual(response.context["public_catalog_page"].start_index(), 1)
        self.assertEqual(response.context["public_catalog_page"].end_index(), 12)
        self.assertEqual(
            response.context["public_catalog_filtered_count"],
            len(PUBLIC_CATALOG_BOOKS),
        )
        self.assertContains(response, 'loading="lazy"')

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_searches_title_author_category_isbn_and_code(self):
        cases = [
            ("Atomic Habits", "Atomic Habits"),
            ("J. K. Rowling", "Harry Potter and the Sorcerer"),
            ("Finance", "Rich Dad Poor Dad"),
            ("9780132350884", "Clean Code"),
            (
                self._code_for_title("The Pragmatic Programmer"),
                "The Pragmatic Programmer",
            ),
            ("Matt Haig", "The Midnight Library"),
            ("9780143130727", "Ikigai"),
            ("Mystery & Thriller", "The Silent Patient"),
            ("BK-2053", "The Silent Patient"),
        ]

        for term, expected_title in cases:
            with self.subTest(term=term):
                response = self.client.get(
                    reverse("library:login"),
                    {"catalog_q": term},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_title)
                self.assertGreaterEqual(self._card_count(response), 1)

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_filters_by_status_and_category(self):
        status_response = self.client.get(
            reverse("library:login"),
            {"catalog_status": "Under Maintenance"},
        )
        category_response = self.client.get(
            reverse("library:login"),
            {"catalog_category": "Finance"},
        )

        self.assertEqual(status_response.status_code, 200)
        self.assertContains(status_response, "Under Maintenance")
        self.assertTrue(
            all(
                book["status"] == "Under Maintenance"
                for book in status_response.context["public_catalog_books"]
            )
        )
        under_maintenance_count = sum(
            1 for book in PUBLIC_CATALOG_BOOKS if book["status"] == "Under Maintenance"
        )
        self.assertEqual(
            status_response.context["public_catalog_filtered_count"],
            under_maintenance_count,
        )
        self.assertEqual(self._card_count(status_response), under_maintenance_count)

        self.assertEqual(category_response.status_code, 200)
        self.assertContains(category_response, "The Psychology of Money")
        self.assertContains(category_response, "Rich Dad Poor Dad")
        self.assertEqual(category_response.context["public_catalog_filtered_count"], 2)
        self.assertEqual(self._card_count(category_response), 2)

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_uses_server_side_pagination(self):
        first_page = self.client.get(reverse("library:login"))
        second_page = self.client.get(
            reverse("library:login"),
            {"catalog_page": 2},
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(self._card_count(first_page), PUBLIC_CATALOG_PAGE_SIZE)
        self.assertEqual(self._card_count(second_page), PUBLIC_CATALOG_PAGE_SIZE)
        self.assertEqual(second_page.context["public_catalog_page"].start_index(), 13)
        self.assertEqual(second_page.context["public_catalog_page"].end_index(), 24)
        self.assertContains(second_page, "The Lean Startup")
        self.assertNotContains(second_page, "Harry Potter and the Sorcerer")

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_combined_filter_empty_state(self):
        response = self.client.get(
            reverse("library:login"),
            {
                "catalog_q": "Harry Potter",
                "catalog_status": "Available",
                "catalog_category": "Finance",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._card_count(response), 0)
        self.assertContains(response, "No matching books found")

    @override_settings(USE_SUPABASE_AUTH=False)
    def test_public_catalog_cards_link_to_detail_pages(self):
        response = self.client.get(reverse("library:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Details")
        self.assertContains(response, "/public/books/BK-2001/?catalog_page=1")

    def test_public_book_detail_page_is_public_and_read_only(self):
        response = self.client.get(self._detail_url("BK-2001"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Harry Potter and the Sorcerer")
        self.assertContains(response, "J. K. Rowling")
        self.assertContains(response, "University Press")
        self.assertContains(response, "9780439708180")
        self.assertContains(response, "BK-2001")
        self.assertContains(response, "Login to Reserve")
        self.assertNotContains(response, "Edit Book")
        self.assertNotContains(response, "Delete Book")

    def test_public_book_detail_invalid_code_returns_404(self):
        response = self.client.get(self._detail_url("BK-9999"))

        self.assertEqual(response.status_code, 404)

    def test_public_book_detail_allows_logged_in_users_without_exposing_staff_actions(
        self,
    ):
        role = Role.objects.create(role_name="Student")
        user = User.objects.create_user(
            username="public-detail-student",
            email="public-detail-student@example.com",
            password="StrongPass123!",
            full_name="Public Detail Student",
            role=role,
        )
        self.client.force_login(user)

        response = self.client.get(self._detail_url(self._code_for_title("The Hobbit")))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Hobbit")
        self.assertContains(response, "Reservation Unavailable")
        self.assertNotContains(response, "Login to Reserve")
        self.assertNotContains(response, "Edit Book")

    def test_public_book_detail_preserves_catalog_state_for_back_link(self):
        response = self.client.get(
            self._detail_url(self._code_for_title("The Psychology of Money")),
            {
                "catalog_q": "Finance",
                "catalog_category": "Finance",
                "catalog_page": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["back_to_catalog_url"],
            "/login/?catalog_q=Finance&catalog_category=Finance&catalog_page=1#public-search",
        )
        self.assertContains(
            response,
            "/login/?catalog_q=Finance&amp;catalog_category=Finance&amp;catalog_page=1#public-search",
        )

    def test_public_book_detail_shows_cover_fallback_and_related_books(self):
        response = self.client.get(
            self._detail_url(self._code_for_title("The Psychology of Money"))
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "psychology_of_money.jpg")
        self.assertContains(response, "fallback_book_cover.svg")
        self.assertContains(response, "More in Finance")
        self.assertContains(response, "Rich Dad Poor Dad")
        self.assertLessEqual(len(response.context["related_books"]), 4)
        self.assertTrue(
            all(
                related["category"] == "Finance"
                for related in response.context["related_books"]
            )
        )

    def test_requested_public_book_detail_pages_render(self):
        cases = [
            ("BK-2051", "The Midnight Library", "Canongate Books"),
            (
                "BK-2052",
                "Ikigai: The Japanese Secret to a Long and Happy Life",
                "Penguin Books",
            ),
            ("BK-2053", "The Silent Patient", "Celadon Books"),
        ]

        for code, title, publisher in cases:
            with self.subTest(code=code):
                response = self.client.get(self._detail_url(code))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, title)
                self.assertContains(response, publisher)
                self.assertContains(response, code)
                self.assertContains(response, "First Edition")

    def test_seed_data_preserves_requested_public_book_metadata(self):
        call_command("seed_data", verbosity=0)

        midnight = Book.objects.select_related("publisher").get(isbn="9780525559474")
        ikigai = Book.objects.select_related("publisher").get(isbn="9780143130727")
        silent = Book.objects.select_related("publisher").get(isbn="9781250301697")

        self.assertEqual(midnight.title, "The Midnight Library")
        self.assertEqual(midnight.publisher.publisher_name, "Canongate Books")
        self.assertEqual(midnight.edition, "First Edition")
        self.assertEqual(midnight.shelf_location, "FIC-A-01")
        self.assertEqual(midnight.quantity, 15)
        self.assertEqual(midnight.available_quantity, 12)
        self.assertEqual(midnight.status, Book.AVAILABLE)

        self.assertEqual(ikigai.publisher.publisher_name, "Penguin Books")
        self.assertEqual(ikigai.edition, "First Edition")
        self.assertEqual(ikigai.shelf_location, "SEL-B-02")
        self.assertEqual(ikigai.quantity, 10)
        self.assertEqual(ikigai.available_quantity, 8)

        self.assertEqual(silent.publisher.publisher_name, "Celadon Books")
        self.assertEqual(silent.edition, "First Edition")
        self.assertEqual(silent.shelf_location, "MYS-C-03")
        self.assertEqual(silent.quantity, 12)
        self.assertEqual(silent.available_quantity, 5)
        self.assertEqual(silent.status, Book.BORROWED)

    def test_seeded_books_have_public_catalog_cover_mapping(self):
        call_command("seed_data", verbosity=0)

        missing_catalog_covers = [
            book.title
            for book in Book.objects.all()
            if book.isbn not in PUBLIC_CATALOG_BY_ISBN
        ]

        self.assertEqual(missing_catalog_covers, [])


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

    @override_settings(FINE_RATE_PER_DAY=Decimal("2.50"))
    def test_late_return_uses_configured_fine_rate(self):
        today = timezone.localdate()
        record = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today - timedelta(days=7),
            due_date=today - timedelta(days=2),
        )

        response = self.client.post(
            reverse("library:borrow_return", args=[record.borrow_id]),
            {"return_date": today},
        )

        self.assertRedirects(response, reverse("library:borrow_list"))
        fine = Fine.objects.get(borrow=record)
        self.assertEqual(fine.amount, Decimal("5.00"))

    def test_return_preserves_special_book_status(self):
        today = timezone.localdate()
        self.book.status = Book.DAMAGED
        self.book.available_quantity = 1
        self.book.save()
        record = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today - timedelta(days=3),
            due_date=today + timedelta(days=7),
        )

        response = self.client.post(
            reverse("library:borrow_return", args=[record.borrow_id]),
            {"return_date": today},
        )

        self.assertRedirects(response, reverse("library:borrow_list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, Book.DAMAGED)
        self.assertEqual(self.book.available_quantity, 2)

    def test_dashboard_does_not_mutate_overdue_status(self):
        today = timezone.localdate()
        record = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
        )

        response = self.client.get(reverse("library:dashboard"))

        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, BorrowRecord.BORROWED)
        self.assertEqual(record.effective_status, BorrowRecord.OVERDUE)

    def test_sync_overdue_command_updates_status_explicitly(self):
        today = timezone.localdate()
        record = BorrowRecord.objects.create(
            member=self.member,
            book=self.book,
            issued_by=self.admin_user,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
        )

        call_command("sync_overdue_records", verbosity=0)

        record.refresh_from_db()
        self.assertEqual(record.status, BorrowRecord.OVERDUE)


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

    def test_admin_book_list_uses_matching_public_catalog_cover(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("library:book_list"), {"q": "Clean Code"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Clean Code")
        self.assertContains(response, "clean_code")
        self.assertContains(response, 'data-book-real-cover="true"')
        self.assertNotContains(response, "data:image/svg")
        self.assertContains(response, PUBLIC_CATALOG_BY_ISBN[self.book.isbn]["code"])

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
    def test_login_page_contains_static_brand_assets(self):
        response = self.client.get(reverse("library:login"))

        self.assertContains(response, "library-login.jpg")
        self.assertContains(response, "library-logo.svg")
        self.assertContains(response, "favicon.svg")

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
        self.assertNotIn("access_token", self.client.session["supabase_auth"])
        self.assertNotIn("refresh_token", self.client.session["supabase_auth"])

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
            "has_session": True,
        }
        session.save()
        service = Mock()

        with patch(
            "apps.library.views.get_supabase_auth_service",
            return_value=service,
        ):
            response = self.client.post(reverse("library:logout"))

        self.assertRedirects(response, reverse("library:login"))
        service.sign_out.assert_not_called()
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

    def test_staff_flag_without_staff_role_cannot_manage_library(self):
        self.member_user.is_staff = True
        self.member_user.save(update_fields=["is_staff", "updated_at"])
        self.client.force_login(self.member_user)

        response = self.client.get(
            reverse("library:entity_list", kwargs={"entity": "users"})
        )

        self.assertEqual(response.status_code, 302)

    def test_librarian_role_cannot_manage_users(self):
        librarian_role = Role.objects.create(role_name="Librarian")
        librarian = User.objects.create_user(
            username="librarian",
            email="librarian@example.com",
            password="StrongPass123!",
            full_name="Role Based Librarian",
            role=librarian_role,
        )
        self.client.force_login(librarian)

        response = self.client.get(
            reverse("library:entity_list", kwargs={"entity": "users"})
        )

        self.assertEqual(response.status_code, 403)


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

    def test_report_upload_rejects_disallowed_extension(self):
        upload = SimpleUploadedFile(
            "manual-report.txt",
            b"not,csv",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("library:report_create"),
            {"report_type": Report.BOOKS, "file_path": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only CSV report files are allowed")
        self.assertFalse(Report.objects.exists())


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

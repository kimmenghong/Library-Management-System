from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Permission, Role

from .forms import BookCopyForm, BookForm, CategoryForm
from .models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf
from .services import generate_qr_svg


User = get_user_model()


class CatalogTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(name="Ada Lovelace", nationality="British")
        cls.publisher = Publisher.objects.create(
            name="University Press",
            contact_email="PRESS@EXAMPLE.COM",
        )
        cls.category = Category.objects.create(name="Computing", code="comp")
        cls.shelf = Shelf.objects.create(
            shelf_code="cs-a1",
            name="Computer Science A1",
            floor="2",
        )
        cls.location = BookLocation.objects.create(
            shelf=cls.shelf,
            label="Row 1",
            aisle="a",
            row="1",
        )
        cls.book = Book.objects.create(
            title="Algorithms and Programming",
            isbn="978-0-262-04630-5",
            book_code="alg-001",
            publisher=cls.publisher,
            category=cls.category,
            publication_year=2024,
            pages=480,
        )
        cls.book.authors.add(cls.author)


class CatalogModelTests(CatalogTestDataMixin, TestCase):
    def test_identifiers_are_normalized(self):
        self.publisher.refresh_from_db()
        self.assertEqual(self.publisher.contact_email, "press@example.com")
        self.assertEqual(self.category.code, "COMP")
        self.assertEqual(self.shelf.shelf_code, "CS-A1")
        self.assertEqual(self.location.aisle, "A")
        self.assertEqual(self.book.isbn, "9780262046305")
        self.assertEqual(self.book.book_code, "ALG-001")

    def test_invalid_isbn_is_rejected(self):
        with self.assertRaisesMessage(ValidationError, "valid ISBN"):
            Book.objects.create(
                title="Invalid ISBN",
                isbn="9780000000000",
                book_code="INVALID-ISBN",
            )

    def test_book_and_copy_codes_are_generated(self):
        generated_book = Book.objects.create(title="Generated Identifier")
        copy = BookCopy.objects.create(book=generated_book)
        self.assertRegex(generated_book.book_code, r"^GENERATE-[A-F0-9]{8}$")
        self.assertRegex(copy.copy_code, rf"^{generated_book.book_code}-C[A-F0-9]{{6}}$")
        self.assertEqual(copy.barcode, copy.copy_code)

    def test_category_cycle_is_rejected(self):
        child = Category.objects.create(name="Child", code="CHILD", parent=self.category)
        self.category.parent = child
        with self.assertRaisesMessage(ValidationError, "cannot contain a cycle"):
            self.category.save()

    def test_copy_location_must_match_shelf(self):
        other_shelf = Shelf.objects.create(shelf_code="CS-B1", name="Other Shelf")
        with self.assertRaisesMessage(ValidationError, "selected shelf"):
            BookCopy.objects.create(
                book=self.book,
                shelf=other_shelf,
                location=self.location,
            )

    def test_location_supplies_shelf_and_price_must_be_non_negative(self):
        copy = BookCopy.objects.create(
            book=self.book,
            location=self.location,
            price=Decimal("25.50"),
        )
        self.assertEqual(copy.shelf, self.shelf)
        self.assertEqual(copy.display_location, self.location)

        with self.assertRaises(ValidationError):
            BookCopy.objects.create(book=self.book, price=Decimal("-1.00"))

    def test_future_acquisition_date_is_rejected(self):
        with self.assertRaisesMessage(ValidationError, "cannot be in the future"):
            BookCopy.objects.create(
                book=self.book,
                acquired_date=timezone.localdate() + timedelta(days=1),
            )

    def test_copy_status_automatically_updates_book_status(self):
        copy = BookCopy.objects.create(book=self.book)
        BookCopy.objects.filter(pk=copy.pk).update(status=BookCopy.BORROWED)
        copy.refresh_from_db()
        copy.save(update_fields=["status", "updated_at"])
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, Book.BORROWED)

        BookCopy.objects.create(book=self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, Book.AVAILABLE)

    def test_book_code_is_immutable_after_copy_registration(self):
        BookCopy.objects.create(book=self.book)
        self.book.book_code = "CHANGED-CODE"
        with self.assertRaisesMessage(ValidationError, "cannot change"):
            self.book.save()

    def test_qr_service_returns_svg(self):
        svg = generate_qr_svg("LMS:BOOK_COPY:TEST-001")
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)


class CatalogFormTests(CatalogTestDataMixin, TestCase):
    def test_operational_status_is_not_editable_in_catalog_forms(self):
        self.assertNotIn("status", BookForm().fields)
        copy_form = BookCopyForm()
        self.assertNotIn("status", copy_form.fields)
        self.assertNotIn("copy_code", copy_form.fields)
        self.assertNotIn("qr_code", copy_form.fields)

    def test_book_form_normalizes_isbn(self):
        second_author = Author.objects.create(name="Grace Hopper")
        form = BookForm(
            data={
                "title": "Compiler Design",
                "isbn": "978-0-13-110362-7",
                "book_code": " comp-001 ",
                "authors": [second_author.pk],
                "language": "english",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.isbn, "9780131103627")
        self.assertEqual(book.book_code, "COMP-001")

    def test_copy_form_rejects_location_from_another_shelf(self):
        other_shelf = Shelf.objects.create(shelf_code="OTHER", name="Other")
        form = BookCopyForm(
            data={
                "book": self.book.pk,
                "shelf": other_shelf.pk,
                "location": self.location.pk,
                "condition": BookCopy.GOOD,
                "acquired_date": timezone.localdate(),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("location", form.errors)

    def test_category_form_excludes_descendants_as_parent(self):
        child = Category.objects.create(name="Child Category", code="CHILD", parent=self.category)
        form = CategoryForm(instance=self.category)
        self.assertNotIn(self.category, form.fields["parent"].queryset)
        self.assertNotIn(child, form.fields["parent"].queryset)


class CatalogViewTests(CatalogTestDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.manager_role = Role.objects.create(name="Catalog Manager", slug="catalog-manager")
        definitions = (
            ("View books", "catalog.view_book", "view"),
            ("Add books", "catalog.add_book", "add"),
            ("Edit books", "catalog.edit_book", "edit"),
            ("Delete books", "catalog.delete_book", "delete"),
            ("Manage authors", "catalog.manage_author", "manage"),
            ("Manage publishers", "catalog.manage_publisher", "manage"),
            ("Manage categories", "catalog.manage_category", "manage"),
            ("Manage copies", "catalog.manage_copy", "manage"),
            ("Manage locations", "catalog.manage_location", "manage"),
        )
        for name, codename, action in definitions:
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": Permission.MODULE_CATALOG,
                    "action": action,
                },
            )
            cls.manager_role.permissions.add(permission)
        cls.manager = User.objects.create_user(
            username="catalog_manager",
            email="catalog.manager@example.com",
            password="StrongPass123!",
            role=cls.manager_role,
        )

    def setUp(self):
        self.client.force_login(self.manager)

    def test_advanced_search_combines_keyword_and_filters(self):
        response = self.client.get(
            reverse("catalog:book_list"),
            {
                "q": "Algorithms Ada",
                "category": self.category.pk,
                "publication_year": 2024,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.book.book_code)

    def test_nested_copy_registration_and_qr_endpoint(self):
        response = self.client.post(
            f"{reverse('catalog:bookcopy_create')}?book={self.book.pk}",
            {
                "book_context": self.book.pk,
                "book": self.book.pk,
                "barcode": "BAR-001",
                "shelf": self.shelf.pk,
                "location": self.location.pk,
                "condition": BookCopy.GOOD,
                "acquired_date": timezone.localdate(),
                "price": "20.00",
            },
        )
        copy = BookCopy.objects.get(barcode="BAR-001")
        self.assertRedirects(
            response,
            reverse("catalog:book_detail", kwargs={"pk": self.book.pk}),
        )

        qr_response = self.client.get(
            reverse("catalog:bookcopy_qr", kwargs={"pk": copy.pk})
        )
        self.assertEqual(qr_response.status_code, 200)
        self.assertEqual(qr_response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertContains(qr_response, "<svg")

    def test_referenced_author_cannot_be_deleted(self):
        response = self.client.post(
            reverse("catalog:author_delete", kwargs={"pk": self.author.pk}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Author.objects.filter(pk=self.author.pk).exists())
        self.assertContains(response, "cannot be deleted")

    def test_book_create_records_actor(self):
        response = self.client.post(
            reverse("catalog:book_create"),
            {
                "title": "Database Systems",
                "book_code": "DB-001",
                "authors": [self.author.pk],
                "language": "English",
            },
        )
        created = Book.objects.get(book_code="DB-001")
        self.assertEqual(created.created_by, self.manager)
        self.assertEqual(created.updated_by, self.manager)
        self.assertRedirects(
            response,
            reverse("catalog:book_detail", kwargs={"pk": created.pk}),
        )


class CatalogAPIValidationTests(CatalogTestDataMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = User.objects.create_superuser(
            username="catalog_api_admin",
            email="catalog.api.admin@example.com",
            password="StrongPass123!",
        )

    def setUp(self):
        self.client.force_authenticate(self.superuser)

    def test_api_rejects_invalid_isbn(self):
        response = self.client.post(
            "/api/books/",
            {
                "title": "Bad ISBN API Book",
                "isbn": "1234567890",
                "book_code": "API-BAD-ISBN",
                "authors": [self.author.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("isbn", response.data)

    def test_api_cannot_set_operational_copy_status(self):
        response = self.client.post(
            "/api/book-copies/",
            {
                "book": self.book.pk,
                "barcode": "API-COPY-001",
                "status": BookCopy.LOST,
                "condition": BookCopy.GOOD,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        copy = BookCopy.objects.get(pk=response.data["id"])
        self.assertEqual(copy.status, BookCopy.AVAILABLE)

import re
from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.library.models import (
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
from apps.library.views import PUBLIC_CATALOG_BOOKS

DEFAULT_PASSWORD = "Library@123"


class Command(BaseCommand):
    help = "Create a repeatable demonstration dataset for the 11-table library schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help="Password assigned to every sample login account.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        roles = self._create_roles()
        users = self._create_users(roles, password)
        categories = self._create_categories()
        authors = self._create_authors()
        publishers = self._create_publishers()
        books = self._create_books(categories, authors, publishers)
        members = self._create_members(users)
        borrows = self._create_borrow_records(members, books, users)
        self._synchronise_book_stock(books)
        self._create_fines(borrows, members)
        self._create_notifications(members, books)
        self._create_reports(users)

        self.stdout.write(self.style.SUCCESS("Sample data created successfully."))
        self.stdout.write("Sample password: %s" % password)
        self.stdout.write(
            "Accounts: sample_admin, sample_librarian, sample_assistant, "
            "sample_student, sample_teacher, sample_staff"
        )

    def _create_roles(self):
        role_descriptions = {
            "Super Admin": "Full control of the Library Management System.",
            "Admin": "Manages users, master data, and reports.",
            "Librarian": "Manages books, borrowing, returns, and fines.",
            "Assistant Librarian": "Assists with daily circulation operations.",
            "Student": "University student library member.",
            "Teacher": "Academic teaching staff library member.",
            "Staff": "University administrative staff library member.",
            "Guest": "Visitor with limited library access.",
        }
        roles = {}
        for name, description in role_descriptions.items():
            role, _ = Role.objects.update_or_create(
                role_name=name,
                defaults={"description": description},
            )
            roles[name] = role
        return roles

    def _create_users(self, roles, password):
        specifications = {
            "admin": {
                "username": "sample_admin",
                "email": "admin@library.test",
                "full_name": "Sophea Library Admin",
                "role": roles["Super Admin"],
                "phone": "012100001",
                "is_staff": True,
                "is_superuser": True,
            },
            "librarian": {
                "username": "sample_librarian",
                "email": "librarian@library.test",
                "full_name": "Dara Librarian",
                "role": roles["Librarian"],
                "phone": "012100002",
                "is_staff": True,
                "is_superuser": False,
            },
            "assistant": {
                "username": "sample_assistant",
                "email": "assistant@library.test",
                "full_name": "Malis Assistant",
                "role": roles["Assistant Librarian"],
                "phone": "012100003",
                "is_staff": True,
                "is_superuser": False,
            },
            "student": {
                "username": "sample_student",
                "email": "student@library.test",
                "full_name": "Sokha Student",
                "role": roles["Student"],
                "phone": "012100004",
                "is_staff": False,
                "is_superuser": False,
            },
            "teacher": {
                "username": "sample_teacher",
                "email": "teacher@library.test",
                "full_name": "Vanna Teacher",
                "role": roles["Teacher"],
                "phone": "012100005",
                "is_staff": False,
                "is_superuser": False,
            },
            "staff": {
                "username": "sample_staff",
                "email": "staff@library.test",
                "full_name": "Bopha Staff",
                "role": roles["Staff"],
                "phone": "012100006",
                "is_staff": False,
                "is_superuser": False,
            },
        }
        users = {}
        for key, values in specifications.items():
            username = values.pop("username")
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    **values,
                    "address": "University Campus, Phnom Penh",
                    "is_active": True,
                },
            )
            user.set_password(password)
            user.save()
            users[key] = user
        return users

    def _create_categories(self):
        values = {
            "Computer Science": "Programming, software, and computing resources.",
            "Business": "Management, accounting, and entrepreneurship resources.",
            "Engineering": "Engineering theory and practical references.",
            "Literature": "Novels, criticism, and language studies.",
            "Comedy": "Humorous stories and light reading.",
            "Fantasy": "Magic, folklore, and imagined worlds.",
            "Adventure": "Action, exploration, and survival stories.",
            "Self-Help": "Personal development and productivity resources.",
            "Fiction": "General novels and literary fiction.",
            "Romance": "Relationship and emotional fiction.",
            "Mystery": "Detective, crime, and puzzle stories.",
            "Horror": "Suspense, fear, and supernatural fiction.",
            "Science Fiction": "Space, technology, and future-focused fiction.",
            "Children's Literature": "Books for young readers.",
            "Finance": "Money, investing, and financial literacy.",
            "Biography": "Life stories and personal histories.",
            "History": "Historical analysis and world events.",
            "Drama": "Plays and dramatic literature.",
            "Productivity": "Focused work and performance improvement.",
            "Memoir": "Personal narratives and reflective life writing.",
            "Programming": "Programming languages, patterns, and software craft.",
            "Networking": "Computer networking and internet architecture.",
            "Operating Systems": "Operating system design and system software.",
            "Database": "Database systems, SQL, and data management.",
            "Artificial Intelligence": "Artificial intelligence and machine learning.",
            "Classic Literature": "Enduring literary works and classic novels.",
        }
        for book in PUBLIC_CATALOG_BOOKS:
            values.setdefault(
                book["category"],
                f"{book['category']} resources for the university library.",
            )
        categories = {}
        for name, description in values.items():
            category, _ = Category.objects.update_or_create(
                category_name=name,
                defaults={"description": description},
            )
            categories[name] = category
        return categories

    def _create_authors(self):
        values = {
            "Robert C. Martin": "Software engineer and author known for Clean Code.",
            "Andrew S. Tanenbaum": "Computer scientist and textbook author.",
            "Thomas H. Cormen": "Computer scientist and algorithms educator.",
            "Jane Austen": "English novelist known for social commentary.",
            "Jeff Kinney": "Author of humorous children's fiction.",
            "J. K. Rowling": "Author of fantasy literature.",
            "J. R. R. Tolkien": "Author of classic fantasy and adventure literature.",
            "James Clear": "Author focused on habits and personal improvement.",
            "Paulo Coelho": "Author of inspirational fiction.",
            "John Green": "Author of contemporary young adult fiction.",
            "Arthur Conan Doyle": "Author of classic detective fiction.",
            "Bram Stoker": "Author of classic gothic horror.",
            "Frank Herbert": "Author of science fiction literature.",
            "Antoine de Saint-Exupery": "Author of children's literature.",
            "Robert Kiyosaki": "Author of personal finance books.",
            "Napoleon Hill": "Author of self-help and success literature.",
            "Morgan Housel": "Author of finance and behavior books.",
            "Suzanne Collins": "Author of adventure and dystopian fiction.",
            "James Dashner": "Author of science fiction and adventure novels.",
            "Harper Lee": "Author of American fiction.",
            "Anne Frank": "Diary author and historical figure.",
            "Walter Isaacson": "Biographer and historian.",
            "Yuval Noah Harari": "Historian and author.",
            "Sun Tzu": "Classical military strategist.",
            "F. Scott Fitzgerald": "Author of American literary fiction.",
            "William Shakespeare": "Playwright and poet.",
            "E. B. White": "Author of children's literature.",
            "Roald Dahl": "Author of children's literature.",
            "Dan Brown": "Author of mystery and thriller fiction.",
            "Stephen King": "Author of horror and suspense fiction.",
            "Stephen R. Covey": "Author of leadership and self-help books.",
            "Kathy Sierra": "Technical author.",
            "Kathy Sierra, Bert Bates": "Technical authors of Head First Java.",
            "Herbert Schildt": "Programming author.",
            "Eric Matthes": "Programming educator and author.",
            "Joshua Bloch": "Software engineer and Java author.",
            "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides": "Authors of Design Patterns.",
            "James Kurose, Keith Ross": "Computer networking textbook authors.",
            "Abraham Silberschatz, Peter B. Galvin, Greg Gagne": "Operating systems textbook authors.",
            "Abraham Silberschatz, Henry F. Korth, S. Sudarshan": "Database systems textbook authors.",
            "Stuart Russell, Peter Norvig": "Artificial intelligence textbook authors.",
            "Cal Newport": "Author of productivity and focus books.",
            "Charles Duhigg": "Author of habit and productivity books.",
            "Khaled Hosseini": "Author of contemporary fiction.",
            "Jojo Moyes": "Author of romance and contemporary fiction.",
            "R. J. Palacio": "Author of children's literature.",
            "Tara Westover": "Memoir author.",
            "Michelle Obama": "Memoir author.",
        }
        for book in PUBLIC_CATALOG_BOOKS:
            values.setdefault(book["author"], f"Author of {book['title']}.")
        authors = {}
        for name, biography in values.items():
            author, _ = Author.objects.update_or_create(
                author_name=name,
                defaults={"biography": biography},
            )
            authors[name] = author
        return authors

    def _create_publishers(self):
        values = {
            "Pearson Education": {
                "address": "London, United Kingdom",
                "contact_number": "+44-20-7010-2000",
                "email": "contact@pearson.test",
            },
            "MIT Press": {
                "address": "Cambridge, Massachusetts",
                "contact_number": "+1-617-253-5646",
                "email": "contact@mitpress.test",
            },
            "University Press": {
                "address": "Phnom Penh, Cambodia",
                "contact_number": "023100200",
                "email": "press@university.test",
            },
        }
        for book in PUBLIC_CATALOG_BOOKS:
            if book.get("publisher"):
                slug = re.sub(r"[^a-z0-9]+", "", book["publisher"].lower())
                values.setdefault(
                    book["publisher"],
                    {
                        "address": "Demonstration publisher address",
                        "contact_number": "000000000",
                        "email": f"contact@{slug or 'publisher'}.test",
                    },
                )
        publishers = {}
        for name, defaults in values.items():
            publisher, _ = Publisher.objects.update_or_create(
                publisher_name=name,
                defaults=defaults,
            )
            publishers[name] = publisher
        return publishers

    def _create_books(self, categories, authors, publishers):
        technical_categories = {
            "AI",
            "Algorithms",
            "Computer Architecture",
            "Computer Science",
            "Database",
            "Networking",
            "Operating Systems",
            "Programming",
            "Software Engineering",
            "Web Development",
        }
        books = {}
        for index, catalog_book in enumerate(PUBLIC_CATALOG_BOOKS, start=1):
            category_name = catalog_book["category"]
            available_copies = int(catalog_book["available_copies"])
            quantity = int(
                catalog_book.get(
                    "total_copies",
                    max(
                        available_copies
                        + (0 if catalog_book["status"] == "Available" else 1),
                        1,
                    ),
                )
            )
            publisher_name = catalog_book.get("publisher") or (
                "Pearson Education"
                if category_name in technical_categories
                else "University Press"
            )
            book, _ = Book.objects.update_or_create(
                isbn=catalog_book["isbn"],
                defaults={
                    "title": catalog_book["title"],
                    "category": categories[category_name],
                    "author": authors[catalog_book["author"]],
                    "publisher": publishers[publisher_name],
                    "edition": catalog_book.get("edition", "Demo"),
                    "publication_year": catalog_book["year"],
                    "quantity": quantity,
                    "available_quantity": available_copies,
                    "shelf_location": catalog_book.get(
                        "shelf_location",
                        f"PUB-{index:03d}",
                    ),
                    "status": (
                        Book.BORROWED
                        if catalog_book["status"] == "Borrowed"
                        else (
                            Book.UNDER_REPAIR
                            if catalog_book["status"] == "Under Maintenance"
                            else Book.AVAILABLE
                        )
                    ),
                },
            )
            books[book.title] = book
        return books

    def _create_members(self, users):
        values = {
            "student": ("STU-2026-001", Member.STUDENT, "Computer Science"),
            "teacher": ("TCH-2026-001", Member.TEACHER, "Information Technology"),
            "staff": ("STF-2026-001", Member.STAFF, "Administration"),
            "librarian": ("LIB-2026-001", Member.LIBRARIAN, "Library Services"),
            "assistant": ("LIB-2026-002", Member.LIBRARIAN, "Library Services"),
        }
        members = {}
        for key, (code, member_type, department) in values.items():
            member, _ = Member.objects.update_or_create(
                user=users[key],
                defaults={
                    "member_code": code,
                    "member_type": member_type,
                    "department": department,
                    "phone": users[key].phone,
                    "address": users[key].address,
                    "status": Member.ACTIVE,
                },
            )
            members[key] = member
        return members

    def _upsert_borrow(self, member, book, defaults):
        record = BorrowRecord.objects.filter(member=member, book=book).first()
        if record is None:
            return BorrowRecord.objects.create(member=member, book=book, **defaults)
        for field, value in defaults.items():
            setattr(record, field, value)
        record.save()
        return record

    def _create_borrow_records(self, members, books, users):
        today = timezone.localdate()
        active = self._upsert_borrow(
            members["student"],
            books["Clean Code"],
            {
                "issued_by": users["librarian"],
                "received_by": None,
                "borrow_date": today - timedelta(days=2),
                "due_date": today + timedelta(days=12),
                "return_date": None,
                "status": BorrowRecord.BORROWED,
            },
        )
        returned = self._upsert_borrow(
            members["teacher"],
            books["Database System Concepts"],
            {
                "issued_by": users["librarian"],
                "received_by": users["assistant"],
                "borrow_date": today - timedelta(days=25),
                "due_date": today - timedelta(days=11),
                "return_date": today - timedelta(days=7),
                "status": BorrowRecord.RETURNED,
            },
        )
        overdue = self._upsert_borrow(
            members["staff"],
            books["Introduction to Algorithms"],
            {
                "issued_by": users["assistant"],
                "received_by": None,
                "borrow_date": today - timedelta(days=20),
                "due_date": today - timedelta(days=6),
                "return_date": None,
                "status": BorrowRecord.OVERDUE,
            },
        )
        return {"active": active, "returned": returned, "overdue": overdue}

    def _synchronise_book_stock(self, books):
        active_statuses = [BorrowRecord.BORROWED, BorrowRecord.OVERDUE]
        for book in books.values():
            record_count = book.borrow_records.count()
            if record_count == 0:
                continue

            active_count = book.borrow_records.filter(
                status__in=active_statuses
            ).count()
            if active_count:
                book.available_quantity = max(book.quantity - active_count, 0)
                book.status = (
                    Book.BORROWED if book.available_quantity == 0 else Book.AVAILABLE
                )
            else:
                book.available_quantity = book.quantity
                book.status = Book.AVAILABLE
            book.save(update_fields=["available_quantity", "status", "updated_at"])

    def _create_fines(self, borrows, members):
        Fine.objects.update_or_create(
            borrow=borrows["returned"],
            member=members["teacher"],
            defaults={
                "amount": Decimal("4.00"),
                "paid_amount": Decimal("2.00"),
                "status": Fine.PARTIALLY_PAID,
                "paid_date": None,
            },
        )

    def _create_notifications(self, members, books):
        values = [
            (
                members["student"],
                "Book due date reminder",
                f"{books['Clean Code'].title} is due in 12 days.",
                Notification.DUE_DATE,
            ),
            (
                members["staff"],
                "Overdue book notice",
                f"{books['Introduction to Algorithms'].title} is overdue.",
                Notification.OVERDUE,
            ),
            (
                members["teacher"],
                "Outstanding fine",
                "A balance of 2.00 remains on your late-return fine.",
                Notification.FINE,
            ),
        ]
        for member, title, message, notification_type in values:
            Notification.objects.update_or_create(
                member=member,
                title=title,
                defaults={
                    "message": message,
                    "notification_type": notification_type,
                    "is_read": False,
                },
            )

    def _create_reports(self, users):
        report, _ = Report.objects.get_or_create(
            report_type=Report.BOOKS,
            generated_by=users["admin"],
        )
        if not report.file_path:
            content = (
                "book_id,title,isbn,status\n"
                + "\n".join(
                    f'{book.book_id},"{book.title}",{book.isbn},{book.status}'
                    for book in Book.objects.order_by("book_id")
                )
                + "\n"
            )
            report.file_path.save(
                "sample_books_report.csv",
                ContentFile(content.encode("utf-8")),
                save=True,
            )

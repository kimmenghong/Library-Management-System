from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Role
from apps.announcements.models import Announcement
from apps.catalog.models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf
from apps.circulation.models import BorrowRecord, BorrowingPolicy, Reservation
from apps.circulation.services import borrow_book, reserve_book, return_book
from apps.digital_library.models import DigitalBook, DigitalBookCategory
from apps.fines.models import Payment
from apps.members.models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.reviews.models import BookReview
from apps.settings_app.models import LibraryProfile, SystemSetting
from apps.status_tracking.models import DamagedBook, RepairRecord
from apps.status_tracking.services import create_repair_record, report_damaged_book
from apps.support.models import FAQ, Feedback, SupportTicket


DEFAULT_PASSWORD = "Password@123"


class Command(BaseCommand):
    help = "Seed realistic sample data for the final Library Management System presentation."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=DEFAULT_PASSWORD)

    def handle(self, *args, **options):
        password = options["password"]
        User = get_user_model()

        roles = {role.slug: role for role in Role.objects.all()}
        admin = self._user(User, "sample_admin", "admin@university.test", "Sample", "Admin", roles.get(Role.SUPER_ADMIN), password, is_staff=True, is_superuser=True)
        librarian = self._user(User, "sample_librarian", "librarian@university.test", "Lina", "Librarian", roles.get(Role.LIBRARIAN), password, is_staff=True)
        assistant = self._user(User, "sample_assistant", "assistant@university.test", "Ari", "Assistant", roles.get(Role.ASSISTANT_LIBRARIAN), password, is_staff=True)
        student_user = self._user(User, "sample_student", "student@university.test", "Sok", "Student", roles.get(Role.STUDENT), password)
        teacher_user = self._user(User, "sample_teacher", "teacher@university.test", "Dara", "Teacher", roles.get(Role.TEACHER), password)
        staff_user = self._user(User, "sample_staff", "staff@university.test", "Mina", "Staff", roles.get(Role.STAFF), password)

        student = self._member(student_user, Member.STUDENT)
        teacher = self._member(teacher_user, Member.TEACHER)
        staff = self._member(staff_user, Member.STAFF)
        librarian_member = self._member(librarian, Member.LIBRARIAN)
        assistant_member = self._member(assistant, Member.ASSISTANT_LIBRARIAN)

        StudentProfile.objects.get_or_create(member=student, defaults={"student_id": "STD-2026-001", "department": "Computer Science", "program": "BSc Information Technology", "year_level": 3, "semester": 1})
        TeacherProfile.objects.get_or_create(member=teacher, defaults={"teacher_id": "TCH-2026-001", "faculty": "Science and Technology", "department": "Computer Science", "designation": "Lecturer"})
        StaffProfile.objects.get_or_create(member=staff, defaults={"staff_id": "STF-2026-001", "department": "Administration", "position": "Registrar"})
        LibrarianProfile.objects.get_or_create(member=librarian_member, defaults={"librarian_id": "LIB-2026-001", "employee_type": LibrarianProfile.FULL_LIBRARIAN, "can_approve_overrides": True})
        LibrarianProfile.objects.get_or_create(member=assistant_member, defaults={"librarian_id": "ALIB-2026-001", "employee_type": LibrarianProfile.ASSISTANT})

        self._policies()
        books = self._catalog(admin)
        self._circulation(student, teacher, staff, librarian_member, librarian, books)
        self._engagement(admin, librarian, student, teacher, staff, books)
        self._settings()

        self.stdout.write(self.style.SUCCESS("Sample data seeded successfully."))
        self.stdout.write("Sample login password for sample users: %s" % password)

    def _user(self, User, username, email, first_name, last_name, role, password, is_staff=False, is_superuser=False):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.save()
        return user

    def _member(self, user, member_type):
        member, _ = Member.objects.get_or_create(
            user=user,
            defaults={
                "member_type": member_type,
                "phone": "012345678",
                "address": "University Campus",
                "status": Member.ACTIVE,
            },
        )
        if member.member_type != member_type or member.status != Member.ACTIVE:
            member.member_type = member_type
            member.status = Member.ACTIVE
            member.save(update_fields=["member_type", "status", "updated_at"])
        return member

    def _policies(self):
        policy_values = {
            Member.STUDENT: (3, 14, 7, 1, Decimal("1.00")),
            Member.TEACHER: (8, 30, 14, 2, Decimal("0.50")),
            Member.STAFF: (5, 21, 7, 1, Decimal("0.75")),
            Member.LIBRARIAN: (6, 21, 7, 2, Decimal("0.50")),
            Member.ASSISTANT_LIBRARIAN: (4, 14, 7, 1, Decimal("0.75")),
        }
        for member_type, values in policy_values.items():
            BorrowingPolicy.objects.update_or_create(
                member_type=member_type,
                defaults={
                    "max_books": values[0],
                    "loan_period_days": values[1],
                    "renewal_days": values[2],
                    "max_renewals": values[3],
                    "fine_per_day": values[4],
                    "reservation_expiry_days": 2,
                    "is_active": True,
                },
            )

    def _catalog(self, admin):
        authors = [
            Author.objects.get_or_create(name="Robert C. Martin", defaults={"nationality": "American"})[0],
            Author.objects.get_or_create(name="Andrew S. Tanenbaum", defaults={"nationality": "Dutch-American"})[0],
            Author.objects.get_or_create(name="Thomas H. Cormen", defaults={"nationality": "American"})[0],
            Author.objects.get_or_create(name="Donald A. Norman", defaults={"nationality": "American"})[0],
        ]
        publisher = Publisher.objects.get_or_create(name="University Press", defaults={"contact_email": "press@university.test"})[0]
        categories = {
            "software": Category.objects.get_or_create(name="Software Engineering", defaults={"code": "SOFTWARE"})[0],
            "network": Category.objects.get_or_create(name="Computer Networks", defaults={"code": "NETWORK"})[0],
            "algorithm": Category.objects.get_or_create(name="Algorithms", defaults={"code": "ALGORITHM"})[0],
            "design": Category.objects.get_or_create(name="Design", defaults={"code": "DESIGN"})[0],
        }
        shelf = Shelf.objects.get_or_create(shelf_code="CS-A1", defaults={"name": "Computer Science A1", "floor": "2", "section": "Technology"})[0]
        location = BookLocation.objects.get_or_create(shelf=shelf, label="Row 1", defaults={"aisle": "A", "row": "1", "column": "1"})[0]
        specs = [
            ("LMS-CLEAN-CODE", "Clean Code", "9780132350884", categories["software"], authors[0], 2024),
            ("LMS-NETWORKS", "Computer Networks", "9780132126953", categories["network"], authors[1], 2023),
            ("LMS-ALGORITHMS", "Introduction to Algorithms", "9780262046305", categories["algorithm"], authors[2], 2022),
            ("LMS-DESIGN", "The Design of Everyday Things", "9780465050659", categories["design"], authors[3], 2021),
        ]
        books = []
        for code, title, isbn, category, author, year in specs:
            book, _ = Book.objects.get_or_create(
                book_code=code,
                defaults={
                    "title": title,
                    "isbn": isbn,
                    "publisher": publisher,
                    "category": category,
                    "publication_year": year,
                    "created_by": admin,
                    "updated_by": admin,
                },
            )
            book.authors.add(author)
            books.append(book)
            for index in range(1, 4):
                BookCopy.objects.get_or_create(
                    book=book,
                    copy_code=f"{code}-C{index:03d}",
                    defaults={"barcode": f"BAR-{code}-{index:03d}", "shelf": shelf, "location": location, "price": Decimal("25.00")},
                )
        return books

    def _circulation(self, student, teacher, staff, librarian_member, librarian, books):
        today = timezone.localdate()
        clean_code, networks, algorithms, design = books
        active_copy = clean_code.copies.filter(copy_code="LMS-CLEAN-CODE-C001").first()
        late_copy = networks.copies.filter(copy_code="LMS-NETWORKS-C001").first()
        damaged_copy = design.copies.filter(copy_code="LMS-DESIGN-C001").first()

        if active_copy and not BorrowRecord.objects.filter(book_copy=active_copy, status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]).exists():
            borrow_book(student, active_copy, librarian, borrow_date=today, due_date=today + timedelta(days=14), notes="Sample active borrow")

        reservation_demo_borrowers = [teacher, staff, librarian_member]
        for copy, borrower in zip(
            algorithms.copies.order_by("copy_code"),
            reservation_demo_borrowers,
            strict=False,
        ):
            if not BorrowRecord.objects.filter(book_copy=copy, status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]).exists():
                borrow_book(
                    borrower,
                    copy,
                    librarian,
                    borrow_date=today,
                    notes="Sample copy made unavailable for reservation demo",
                )

        if not Reservation.objects.filter(member=student, book=algorithms, status__in=[Reservation.PENDING, Reservation.READY]).exists():
            reserve_book(student, algorithms, notes="Sample reservation for unavailable book")

        if late_copy and not BorrowRecord.objects.filter(book_copy=late_copy, return_date__isnull=False).exists():
            record = borrow_book(staff, late_copy, librarian, borrow_date=today - timedelta(days=20), due_date=today - timedelta(days=5), notes="Sample late return")
            return_book(record, librarian, return_date=today, remarks="Returned after due date")

        if damaged_copy and not DamagedBook.objects.filter(book_copy=damaged_copy).exists():
            damaged = report_damaged_book(damaged_copy, reported_by=librarian, member=staff, severity=DamagedBook.MODERATE, estimated_repair_cost=Decimal("8.50"), description="Sample torn pages")
            if not RepairRecord.objects.filter(book_copy=damaged_copy).exists():
                create_repair_record(damaged_copy, sent_by=librarian, damage_record=damaged, vendor="Campus Bindery", expected_return_date=today + timedelta(days=10), repair_cost=Decimal("8.50"), notes="Sample repair job")

        fine = staff.fines.exclude(status__in=["paid", "waived"]).first()
        if fine and not fine.payments.exists():
            Payment.objects.create(fine=fine, member=staff, amount_paid=min(fine.amount, Decimal("2.00")), payment_method=Payment.CASH, received_by=librarian, notes="Sample partial payment")

    def _engagement(self, admin, librarian, student, teacher, staff, books):
        category = DigitalBookCategory.objects.get_or_create(name="Course Materials", defaults={"description": "PDF and eBook resources"})[0]
        digital, created = DigitalBook.objects.get_or_create(
            title="Clean Code Lecture Notes",
            defaults={"book": books[0], "category": category, "description": "Sample PDF for digital library.", "is_public": True, "uploaded_by": librarian},
        )
        if created or not digital.file:
            digital.file.save("clean_code_notes.pdf", ContentFile(b"%PDF-1.4 sample final project notes"), save=True)

        BookReview.objects.get_or_create(book=books[0], member=student, defaults={"rating": 5, "review_text": "Excellent practical programming book.", "status": BookReview.APPROVED, "moderated_by": librarian})
        BookReview.objects.get_or_create(book=books[1], member=teacher, defaults={"rating": 4, "review_text": "Useful for network fundamentals.", "status": BookReview.PENDING})

        Announcement.objects.get_or_create(
            title="Final Exam Reading Week",
            defaults={"content": "Extended library hours are available during final exam reading week.", "status": Announcement.PUBLISHED, "created_by": admin, "publish_date": timezone.now()},
        )
        FAQ.objects.get_or_create(question="How many books can a student borrow?", defaults={"answer": "Students can borrow up to 3 books based on the default borrowing policy.", "category": "Borrowing", "display_order": 1})
        SupportTicket.objects.get_or_create(subject="Request for research support", defaults={"message": "Need help finding algorithm references.", "priority": SupportTicket.NORMAL, "user": student.user, "assigned_to": librarian})
        Feedback.objects.get_or_create(name="Sample Student", defaults={"email": "student@university.test", "rating": 5, "message": "The library system is easy to use.", "user": student.user})
        create_notification(
            recipient=student,
            title="Welcome to the Library Management System",
            message="Your student account is ready for borrowing and reservations.",
            notification_type=Notification.SYSTEM,
            created_by=librarian,
        )

    def _settings(self):
        LibraryProfile.objects.update_or_create(
            pk=1,
            defaults={
                "name": "University Central Library",
                "address": "Main Campus, Academic Road",
                "phone": "012345678",
                "email": "library@university.test",
                "website": "https://library.university.test",
                "theme": "default",
            },
        )
        SystemSetting.objects.update_or_create(key="fine.default_rate", defaults={"value": "1.00", "description": "Default fine amount per late day."})
        SystemSetting.objects.update_or_create(key="email.reminders_enabled", defaults={"value": "true", "description": "Controls automated reminder sending."})

from decimal import Decimal

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Role(models.Model):
    """A high-level access role assigned to application users."""

    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "roles"
        ordering = ["role_name"]

    def __str__(self):
        return self.role_name


class UserManager(BaseUserManager):
    """Create normalized custom users for the lecturer-defined users table."""

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("The username is required.")
        if not email:
            raise ValueError("The email address is required.")
        email = self.normalize_email(email)
        user = self.model(
            username=username.strip(),
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    """Custom authentication model backed by the required `users` table."""

    user_id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        db_column="role_id",
    )
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "full_name", "role"]

    class Meta:
        db_table = "users"
        ordering = ["username"]
        indexes = [
            models.Index(fields=["role", "is_active"], name="users_role_active_idx"),
            models.Index(
                fields=["is_staff", "is_active"],
                name="users_staff_active_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.username = self.username.strip()
        self.email = self.__class__.objects.normalize_email(self.email)
        self.full_name = self.full_name.strip()
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        return bool(self.is_active and (self.is_superuser or self.is_staff))

    def has_module_perms(self, app_label):
        return self.has_perm(app_label)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.username

    @property
    def can_manage_library(self):
        if self.is_superuser or self.is_staff:
            return True
        staff_roles = {
            "super admin",
            "admin",
            "librarian",
            "assistant librarian",
        }
        return bool(self.role_id and self.role.role_name.strip().lower() in staff_roles)

    def __str__(self):
        return self.username


class Category(models.Model):
    """Book category master data."""

    category_id = models.BigAutoField(primary_key=True)
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "categories"
        ordering = ["category_name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.category_name


class Author(models.Model):
    """Book author master data."""

    author_id = models.BigAutoField(primary_key=True)
    author_name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["author_name"]

    def __str__(self):
        return self.author_name


class Publisher(models.Model):
    """Book publisher master data."""

    publisher_id = models.BigAutoField(primary_key=True)
    publisher_name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True)

    class Meta:
        db_table = "publishers"
        ordering = ["publisher_name"]

    def __str__(self):
        return self.publisher_name


class Book(models.Model):
    """Catalog and stock record for a title in the required books table."""

    AVAILABLE = "available"
    BORROWED = "borrowed"
    LOST = "lost"
    DAMAGED = "damaged"
    UNDER_REPAIR = "under_repair"
    STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (BORROWED, "Borrowed"),
        (LOST, "Lost"),
        (DAMAGED, "Damaged"),
        (UNDER_REPAIR, "Under Repair"),
    ]

    book_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="books",
        db_column="category_id",
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
        db_column="author_id",
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="books",
        db_column="publisher_id",
    )
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    edition = models.CharField(max_length=50, blank=True)
    publication_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(9999)],
    )
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    shelf_location = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AVAILABLE,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "books"
        ordering = ["title"]
        indexes = [
            models.Index(
                fields=["status", "available_quantity"],
                name="books_status_available_idx",
            ),
            models.Index(
                fields=["category", "status"],
                name="books_category_status_idx",
            ),
            models.Index(fields=["title"], name="books_title_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="books_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(available_quantity__gte=0),
                name="books_available_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(available_quantity__lte=F("quantity")),
                name="books_available_not_above_quantity",
            ),
        ]

    def clean(self):
        errors = {}
        if self.available_quantity > self.quantity:
            errors["available_quantity"] = (
                "Available quantity cannot exceed total quantity."
            )
        if self.publication_year and self.publication_year > timezone.localdate().year:
            errors["publication_year"] = "Publication year cannot be in the future."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.isbn = self.isbn.replace("-", "").replace(" ", "").upper()
        self.title = self.title.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Member(models.Model):
    """Library member profile linked one-to-one with a user account."""

    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"
    LIBRARIAN = "librarian"
    MEMBER_TYPE_CHOICES = [
        (STUDENT, "Student"),
        (TEACHER, "Teacher"),
        (STAFF, "Staff"),
        (LIBRARIAN, "Librarian"),
    ]

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (SUSPENDED, "Suspended"),
        (EXPIRED, "Expired"),
    ]

    member_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="member",
        db_column="user_id",
    )
    member_code = models.CharField(max_length=30, unique=True)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    registration_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)

    class Meta:
        db_table = "members"
        ordering = ["member_code"]
        indexes = [
            models.Index(
                fields=["member_type", "status"],
                name="members_type_status_idx",
            ),
            models.Index(fields=["status"], name="members_status_idx"),
        ]

    def save(self, *args, **kwargs):
        self.member_code = self.member_code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_code} - {self.user.full_name}"


class BorrowRecord(models.Model):
    """Title-level borrowing transaction required by the lecturer schema."""

    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"
    STATUS_CHOICES = [
        (BORROWED, "Borrowed"),
        (RETURNED, "Returned"),
        (OVERDUE, "Overdue"),
        (LOST, "Lost"),
    ]

    borrow_id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="borrow_records",
        db_column="member_id",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name="borrow_records",
        db_column="book_id",
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="issued_borrow_records",
        db_column="issued_by",
    )
    received_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="received_borrow_records",
        db_column="received_by",
    )
    borrow_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=BORROWED,
    )

    class Meta:
        db_table = "borrow_records"
        ordering = ["-borrow_date", "-borrow_id"]
        indexes = [
            models.Index(fields=["status", "due_date"], name="borrow_status_due_idx"),
            models.Index(fields=["member", "status"], name="borrow_member_status_idx"),
            models.Index(fields=["book", "status"], name="borrow_book_status_idx"),
            models.Index(
                fields=["issued_by", "borrow_date"],
                name="borrow_issued_date_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(due_date__gte=F("borrow_date")),
                name="borrow_due_on_or_after_borrow",
            ),
            models.CheckConstraint(
                condition=Q(return_date__isnull=True)
                | Q(return_date__gte=F("borrow_date")),
                name="borrow_return_on_or_after_borrow",
            ),
        ]

    def clean(self):
        errors = {}
        if self.due_date and self.borrow_date and self.due_date < self.borrow_date:
            errors["due_date"] = "Due date cannot be earlier than borrow date."
        if (
            self.return_date
            and self.borrow_date
            and self.return_date < self.borrow_date
        ):
            errors["return_date"] = "Return date cannot be earlier than borrow date."
        if self.status == self.RETURNED:
            if not self.return_date:
                errors["return_date"] = "A returned book requires a return date."
            if not self.received_by_id:
                errors["received_by"] = "A returned book requires a receiving user."
        elif self.return_date or self.received_by_id:
            errors["status"] = "Only returned borrow records can have return details."
        if errors:
            raise ValidationError(errors)

    @property
    def days_overdue(self):
        comparison_date = self.return_date or timezone.localdate()
        return max((comparison_date - self.due_date).days, 0)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Borrow #{self.borrow_id}: {self.book.title}"


class Fine(models.Model):
    """Fine record linked to a borrow transaction and its member."""

    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    WAIVED = "waived"
    STATUS_CHOICES = [
        (UNPAID, "Unpaid"),
        (PARTIALLY_PAID, "Partially Paid"),
        (PAID, "Paid"),
        (WAIVED, "Waived"),
    ]

    fine_id = models.BigAutoField(primary_key=True)
    borrow = models.ForeignKey(
        BorrowRecord,
        on_delete=models.PROTECT,
        related_name="fines",
        db_column="borrow_id",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="fines",
        db_column="member_id",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UNPAID)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    paid_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "fines"
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="fines_status_created_idx",
            ),
            models.Index(fields=["member", "status"], name="fines_member_status_idx"),
            models.Index(fields=["borrow"], name="fines_borrow_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="fines_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(paid_amount__gte=0) & Q(paid_amount__lte=F("amount")),
                name="fines_paid_amount_valid",
            ),
        ]

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def clean(self):
        errors = {}
        if (
            self.borrow_id
            and self.member_id
            and self.borrow.member_id != self.member_id
        ):
            errors["member"] = "Fine member must match the borrow record member."
        if self.paid_amount > self.amount:
            errors["paid_amount"] = "Paid amount cannot exceed the fine amount."
        if self.status == self.PAID and self.paid_amount != self.amount:
            errors["status"] = "A paid fine must be paid in full."
        if self.status == self.PAID and not self.paid_date:
            errors["paid_date"] = "A paid fine requires a paid date."
        if self.status != self.PAID and self.paid_date:
            errors["paid_date"] = "Only paid fines can have a paid date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fine #{self.fine_id} - {self.member.member_code}"


class Notification(models.Model):
    """Notification history addressed to a library member."""

    DUE_DATE = "due_date"
    OVERDUE = "overdue"
    FINE = "fine"
    GENERAL = "general"
    TYPE_CHOICES = [
        (DUE_DATE, "Due Date"),
        (OVERDUE, "Overdue"),
        (FINE, "Fine"),
        (GENERAL, "General"),
    ]

    notification_id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_column="member_id",
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=GENERAL,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["member", "is_read"],
                name="notifications_member_read_idx",
            ),
            models.Index(
                fields=["notification_type", "created_at"],
                name="notifications_type_created_idx",
            ),
        ]

    def __str__(self):
        return self.title


class Report(models.Model):
    """Generated report metadata and optional report file."""

    BOOKS = "books"
    MEMBERS = "members"
    BORROWING = "borrowing"
    FINES = "fines"
    TYPE_CHOICES = [
        (BOOKS, "Books"),
        (MEMBERS, "Members"),
        (BORROWING, "Borrowing"),
        (FINES, "Fines"),
    ]

    report_id = models.BigAutoField(primary_key=True)
    report_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="generated_reports",
        db_column="generated_by",
    )
    generated_at = models.DateTimeField(default=timezone.now, editable=False)
    file_path = models.FileField(upload_to="reports/", max_length=255, blank=True)

    class Meta:
        db_table = "reports"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(
                fields=["report_type", "generated_at"],
                name="reports_type_generated_idx",
            ),
            models.Index(
                fields=["generated_by", "generated_at"],
                name="reports_user_generated_idx",
            ),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} report #{self.report_id}"

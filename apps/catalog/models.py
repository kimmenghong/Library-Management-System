import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.text import slugify


phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9 ()-]{6,24}$",
    message="Enter a valid phone number using digits, spaces, parentheses, +, or -.",
)
image_extension_validator = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])


def validate_catalog_image_size(upload):
    if upload.size > settings.MAX_UPLOAD_SIZE:
        maximum_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f"Image size cannot exceed {maximum_mb} MB.")


def normalize_isbn(value):
    if not value:
        return None
    return re.sub(r"[-\s]", "", str(value)).upper()


def validate_isbn(value):
    isbn = normalize_isbn(value)
    if not isbn:
        return
    if len(isbn) == 10 and re.fullmatch(r"\d{9}[\dX]", isbn):
        total = sum((10 - index) * (10 if char == "X" else int(char)) for index, char in enumerate(isbn))
        if total % 11 == 0:
            return
    if len(isbn) == 13 and isbn.isdigit():
        total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(isbn))
        if total % 10 == 0:
            return
    raise ValidationError("Enter a valid ISBN-10 or ISBN-13.")


def unique_slug_for(instance, name):
    base_slug = slugify(name)[:180] or uuid.uuid4().hex[:12]
    candidate = base_slug
    index = 1
    model = type(instance)
    while model.objects.filter(slug=candidate).exclude(pk=instance.pk).exists():
        index += 1
        suffix = f"-{index}"
        candidate = f"{base_slug[: 200 - len(suffix)]}{suffix}"
    return candidate


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Author(TimeStampedModel):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True, editable=False)
    biography = models.TextField(blank=True)
    nationality = models.CharField(max_length=120, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(
        upload_to="authors/photos/",
        blank=True,
        validators=[image_extension_validator, validate_catalog_image_size],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.slug:
            self.slug = unique_slug_for(self, self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Publisher(TimeStampedModel):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, editable=False)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="publisher_name_ci_unique")
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.contact_email = self.contact_email.strip().lower()
        if not self.slug:
            self.slug = unique_slug_for(self, self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(TimeStampedModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True, editable=False)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(Lower("code"), name="category_code_ci_unique")
        ]

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "A category cannot be its own parent."})
        ancestor = self.parent
        visited = set()
        while ancestor:
            if ancestor.pk == self.pk or ancestor.pk in visited:
                raise ValidationError({"parent": "Category hierarchy cannot contain a cycle."})
            visited.add(ancestor.pk)
            ancestor = ancestor.parent

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.code = self.code.strip().upper()
        if not self.slug:
            self.slug = unique_slug_for(self, self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.parent.name} / {self.name}" if self.parent else self.name

    def __str__(self):
        return self.full_name


class Shelf(TimeStampedModel):
    shelf_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    floor = models.CharField(max_length=80, blank=True)
    section = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shelf_code"]
        constraints = [
            models.UniqueConstraint(Lower("shelf_code"), name="shelf_code_ci_unique")
        ]

    def save(self, *args, **kwargs):
        self.shelf_code = self.shelf_code.strip().upper()
        self.name = self.name.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shelf_code} - {self.name}"


class BookLocation(TimeStampedModel):
    shelf = models.ForeignKey(Shelf, on_delete=models.PROTECT, related_name="locations")
    aisle = models.CharField(max_length=50, blank=True)
    row = models.CharField(max_length=50, blank=True)
    column = models.CharField(max_length=50, blank=True)
    label = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shelf__shelf_code", "label"]
        constraints = [
            models.UniqueConstraint(
                Lower("label"),
                "shelf",
                name="location_label_per_shelf_ci_unique",
            )
        ]

    def save(self, *args, **kwargs):
        self.label = self.label.strip()
        self.aisle = self.aisle.strip().upper()
        self.row = self.row.strip().upper()
        self.column = self.column.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shelf.shelf_code} / {self.label}"


class Book(TimeStampedModel):
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

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_isbn],
    )
    book_code = models.CharField(max_length=50, unique=True, blank=True)
    authors = models.ManyToManyField(Author, related_name="books")
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="books",
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="books",
    )
    publication_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(9999)],
    )
    edition = models.CharField(max_length=80, blank=True)
    language = models.CharField(max_length=80, default="English")
    pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="book_covers/",
        blank=True,
        validators=[image_extension_validator, validate_catalog_image_size],
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=AVAILABLE,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_books",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_books",
    )

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["title"]), models.Index(fields=["status"])]
        constraints = [
            models.UniqueConstraint(Lower("book_code"), name="book_code_ci_unique"),
            models.CheckConstraint(
                condition=Q(pages__isnull=True) | Q(pages__gte=1),
                name="book_pages_positive",
            ),
        ]

    def clean(self):
        errors = {}
        if self.publication_year and self.publication_year > timezone.localdate().year + 1:
            errors["publication_year"] = "Publication year cannot be more than one year in the future."
        if self.pk:
            previous_code = (
                Book.objects.filter(pk=self.pk).values_list("book_code", flat=True).first()
            )
            if previous_code and previous_code != self.book_code and self.copies.exists():
                errors["book_code"] = "Book code cannot change after copies have been registered."
        if errors:
            raise ValidationError(errors)

    def _generate_book_code(self):
        prefix = re.sub(r"[^A-Z0-9]", "", self.title.upper())[:8] or "BOOK"
        for _attempt in range(10):
            candidate = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
            if not Book.objects.filter(book_code=candidate).exists():
                return candidate
        raise RuntimeError("Unable to generate a unique book code.")

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.subtitle = self.subtitle.strip()
        self.language = self.language.strip().title() or "English"
        self.isbn = normalize_isbn(self.isbn)
        self.book_code = self.book_code.strip().upper() if self.book_code else self._generate_book_code()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_copies(self):
        return self.copies.count()

    @property
    def available_copies(self):
        return self.copies.filter(status=BookCopy.AVAILABLE).count()

    @property
    def author_names(self):
        return ", ".join(author.name for author in self.authors.all())

    def __str__(self):
        return f"{self.title} ({self.book_code})"


class BookCopy(TimeStampedModel):
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

    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED_CONDITION = "damaged"

    CONDITION_CHOICES = [
        (NEW, "New"),
        (GOOD, "Good"),
        (FAIR, "Fair"),
        (POOR, "Poor"),
        (DAMAGED_CONDITION, "Damaged"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    copy_code = models.CharField(max_length=80, unique=True, blank=True, editable=False)
    barcode = models.CharField(max_length=120, unique=True, null=True, blank=True)
    qr_code = models.FileField(upload_to="qr_codes/", blank=True, editable=False)
    shelf = models.ForeignKey(
        Shelf,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="book_copies",
    )
    location = models.ForeignKey(
        BookLocation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="book_copies",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=AVAILABLE,
        editable=False,
    )
    condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, default=GOOD)
    acquired_date = models.DateField(default=timezone.localdate)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["book__title", "copy_code"]
        verbose_name_plural = "Book copies"
        indexes = [models.Index(fields=["status"]), models.Index(fields=["acquired_date"])]
        constraints = [
            models.UniqueConstraint(Lower("copy_code"), name="copy_code_ci_unique"),
            models.UniqueConstraint(Lower("barcode"), name="barcode_ci_unique"),
            models.CheckConstraint(
                condition=Q(price__isnull=True) | Q(price__gte=0),
                name="book_copy_price_non_negative",
            ),
        ]

    def clean(self):
        errors = {}
        if self.location_id and self.shelf_id and self.location.shelf_id != self.shelf_id:
            errors["location"] = "Book location must belong to the selected shelf."
        if self.acquired_date and self.acquired_date > timezone.localdate():
            errors["acquired_date"] = "Acquired date cannot be in the future."
        if self.condition == self.DAMAGED_CONDITION and self.status in {
            self.AVAILABLE,
            self.BORROWED,
        }:
            errors["condition"] = "A damaged copy must be recorded as damaged or under repair."
        if self.pk:
            previous = BookCopy.objects.filter(pk=self.pk).values("book_id", "copy_code").first()
            if previous and previous["book_id"] != self.book_id:
                errors["book"] = "A registered copy cannot be moved to another book."
            if previous and previous["copy_code"] != self.copy_code:
                errors["copy_code"] = "Copy code cannot be changed after registration."
        if errors:
            raise ValidationError(errors)

    def _generate_copy_code(self):
        for _attempt in range(10):
            candidate = f"{self.book.book_code}-C{uuid.uuid4().hex[:6].upper()}"
            if not BookCopy.objects.filter(copy_code=candidate).exists():
                return candidate
        raise RuntimeError("Unable to generate a unique copy code.")

    def save(self, *args, **kwargs):
        if not self.copy_code and self.book_id:
            self.copy_code = self._generate_copy_code()
        self.copy_code = self.copy_code.strip().upper()
        self.barcode = self.barcode.strip().upper() if self.barcode else self.copy_code
        if self.location_id and not self.shelf_id:
            self.shelf = self.location.shelf
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def qr_payload(self):
        return f"LMS:BOOK_COPY:{self.barcode}"

    @property
    def display_location(self):
        return self.location or self.shelf

    def __str__(self):
        return f"{self.copy_code} - {self.book.title}"

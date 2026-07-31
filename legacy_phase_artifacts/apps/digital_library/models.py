from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Role
from apps.catalog.models import Book


def validate_digital_file(value):
    allowed = {".pdf", ".epub", ".mobi", ".azw3", ".txt"}
    extension = Path(value.name).suffix.lower()
    if extension not in allowed:
        raise ValidationError("Only PDF, EPUB, MOBI, AZW3, and TXT files are allowed.")


class DigitalBookCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Digital book categories"

    def __str__(self):
        return self.name


class DigitalBook(models.Model):
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    AZW3 = "azw3"
    TXT = "txt"

    FILE_TYPE_CHOICES = [
        (PDF, "PDF"),
        (EPUB, "EPUB"),
        (MOBI, "MOBI"),
        (AZW3, "AZW3"),
        (TXT, "TXT"),
    ]

    title = models.CharField(max_length=255)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.SET_NULL, related_name="digital_books")
    category = models.ForeignKey(DigitalBookCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="digital_books")
    file = models.FileField(upload_to="digital_books/", validators=[validate_digital_file])
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default=PDF)
    description = models.TextField(blank=True)
    allowed_roles = models.ManyToManyField(Role, blank=True, related_name="digital_books")
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    download_count = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_digital_books")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def clean(self):
        super().clean()
        if self.file:
            extension = Path(self.file.name).suffix.lower().replace(".", "")
            if extension:
                self.file_type = extension

    def can_access(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.has_role_permission("digital.manage_digital_book"):
            return True
        if not self.is_active:
            return False
        if self.is_public:
            return True
        if not user.role:
            return False
        return self.allowed_roles.filter(pk=user.role_id).exists()

    def __str__(self):
        return self.title

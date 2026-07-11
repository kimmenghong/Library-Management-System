from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


def validate_avatar_size(upload):
    """Reject unexpectedly large profile images before they reach storage."""
    if upload.size > settings.PROFILE_IMAGE_MAX_SIZE:
        maximum_mb = settings.PROFILE_IMAGE_MAX_SIZE // (1024 * 1024)
        raise ValidationError(f"Profile image size cannot exceed {maximum_mb} MB.")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Permission(TimeStampedModel):
    MODULE_ACCOUNTS = "accounts"
    MODULE_MEMBERS = "members"
    MODULE_CATALOG = "catalog"
    MODULE_CIRCULATION = "circulation"
    MODULE_FINES = "fines"
    MODULE_NOTIFICATIONS = "notifications"
    MODULE_STATUS_TRACKING = "status_tracking"
    MODULE_DASHBOARD = "dashboard"
    MODULE_REPORTS = "reports"
    MODULE_ACTIVITY = "activity"
    MODULE_DIGITAL = "digital"
    MODULE_REVIEWS = "reviews"
    MODULE_ANNOUNCEMENTS = "announcements"
    MODULE_SUPPORT = "support"
    MODULE_SETTINGS = "settings"
    MODULE_IMPORT_EXPORT = "import_export"

    MODULE_CHOICES = [
        (MODULE_ACCOUNTS, "Authentication and Users"),
        (MODULE_MEMBERS, "Members"),
        (MODULE_CATALOG, "Books and Catalog"),
        (MODULE_CIRCULATION, "Borrowing and Returning"),
        (MODULE_FINES, "Fines and Payments"),
        (MODULE_NOTIFICATIONS, "Notifications"),
        (MODULE_STATUS_TRACKING, "Book Status Tracking"),
        (MODULE_DASHBOARD, "Dashboard"),
        (MODULE_REPORTS, "Reports and Analytics"),
        (MODULE_ACTIVITY, "Activity and Audit Logs"),
        (MODULE_DIGITAL, "Digital Library"),
        (MODULE_REVIEWS, "Book Reviews"),
        (MODULE_ANNOUNCEMENTS, "Announcements"),
        (MODULE_SUPPORT, "Help and Support"),
        (MODULE_SETTINGS, "System Settings"),
        (MODULE_IMPORT_EXPORT, "Import and Export"),
    ]

    ACTION_CHOICES = [
        ("view", "View"),
        ("add", "Add"),
        ("edit", "Edit"),
        ("delete", "Delete"),
        ("approve", "Approve"),
        ("export", "Export"),
        ("import", "Import"),
        ("manage", "Manage"),
    ]

    name = models.CharField(max_length=150)
    codename = models.CharField(max_length=150, unique=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["module", "action", "name"]

    def __str__(self):
        return self.codename


class Role(TimeStampedModel):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    ASSISTANT_LIBRARIAN = "assistant_librarian"
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"
    GUEST = "guest"

    SYSTEM_ROLE_CHOICES = [
        (SUPER_ADMIN, "Super Admin"),
        (ADMIN, "Admin"),
        (LIBRARIAN, "Librarian"),
        (ASSISTANT_LIBRARIAN, "Assistant Librarian"),
        (STUDENT, "Student"),
        (TEACHER, "Teacher"),
        (STAFF, "Staff"),
        (GUEST, "Guest / Visitor"),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = Role.objects.filter(pk=self.pk).only("slug", "is_system").first()
            if previous and previous.is_system:
                self.slug = previous.slug
                self.is_system = True
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def has_permission(self, codename):
        if not self.is_active:
            return False
        return self.permissions.filter(codename=codename, is_active=True).exists()

    def __str__(self):
        return self.name


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="profiles/avatars/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_avatar_size,
        ],
    )
    must_change_password = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["username"]

    @property
    def full_name(self):
        name = self.get_full_name().strip()
        return name or self.username

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def has_role_permission(self, codename):
        if self.is_superuser:
            return True
        if not self.is_active or not self.role:
            return False
        if not self.role.is_active:
            return False
        if not hasattr(self, "_role_permission_codenames"):
            self._role_permission_codenames = set(
                self.role.permissions.filter(is_active=True).values_list(
                    "codename", flat=True
                )
            )
        return codename in self._role_permission_codenames

    def has_role(self, *role_slugs):
        if self.is_superuser:
            return True
        return bool(self.role and self.role.is_active and self.role.slug in role_slugs)

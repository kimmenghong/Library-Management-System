import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class LibraryProfile(models.Model):
    name = models.CharField(max_length=180, default="University Library")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.FileField(upload_to="settings/logo/", blank=True)
    theme = models.CharField(max_length=40, default="default")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SystemSetting(models.Model):
    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class BackupSchedule(models.Model):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    FREQUENCY_CHOICES = [
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
    ]

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default=DAILY)
    backup_time = models.TimeField(default=datetime.time(23, 0))
    is_enabled = models.BooleanField(default=False)
    backup_directory = models.CharField(max_length=255, default="backups")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_frequency_display()} backup"


class BackupRecord(models.Model):
    CREATED = "created"
    RESTORED = "restored"
    FAILED = "failed"

    STATUS_CHOICES = [
        (CREATED, "Created"),
        (RESTORED, "Restored"),
        (FAILED, "Failed"),
    ]

    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CREATED)
    message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="backup_records")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.file_name

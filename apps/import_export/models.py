from django.conf import settings
from django.db import models


class ImportJob(models.Model):
    BOOKS = "books"
    TARGET_CHOICES = [(BOOKS, "Books")]

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    target = models.CharField(max_length=40, choices=TARGET_CHOICES, default=BOOKS)
    source_file = models.FileField(upload_to="imports/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_rows = models.PositiveIntegerField(default=0)
    success_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="import_jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_target_display()} import #{self.pk}"


class ExportJob(models.Model):
    BOOKS = "books"
    MEMBERS = "members"
    BORROW_RECORDS = "borrow_records"
    FINES = "fines"

    TARGET_CHOICES = [
        (BOOKS, "Books"),
        (MEMBERS, "Members"),
        (BORROW_RECORDS, "Borrowing Records"),
        (FINES, "Fines"),
    ]

    target = models.CharField(max_length=40, choices=TARGET_CHOICES)
    file_format = models.CharField(max_length=20, default="csv")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="export_jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_target_display()} export #{self.pk}"

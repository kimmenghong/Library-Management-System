from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Role


class Announcement(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
        (UNPUBLISHED, "Unpublished"),
    ]

    title = models.CharField(max_length=180)
    content = models.TextField()
    target_roles = models.ManyToManyField(Role, blank=True, related_name="announcements")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    publish_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(null=True, blank=True)
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_announcements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_date"]

    @property
    def is_visible(self):
        now = timezone.now()
        return self.status == self.PUBLISHED and self.publish_date <= now and (not self.expire_date or self.expire_date >= now)

    def __str__(self):
        return self.title

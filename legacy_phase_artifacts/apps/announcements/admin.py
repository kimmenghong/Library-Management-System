from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "publish_date", "expire_date", "send_email", "email_sent")
    list_filter = ("status", "send_email", "email_sent", "publish_date")
    search_fields = ("title", "content")
    filter_horizontal = ("target_roles",)
    autocomplete_fields = ("created_by",)

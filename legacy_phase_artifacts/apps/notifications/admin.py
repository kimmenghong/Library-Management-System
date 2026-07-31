from django.contrib import admin

from .models import EmailReminder, Notification


class ReadOnlyDeliveryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(ReadOnlyDeliveryAdmin):
    list_display = (
        "recipient",
        "title",
        "notification_type",
        "channel",
        "priority",
        "status",
        "is_email_sent",
        "created_at",
    )
    list_filter = ("notification_type", "channel", "priority", "status", "is_email_sent")
    search_fields = (
        "recipient__member_code",
        "recipient__user__username",
        "title",
        "message",
        "deduplication_key",
    )
    list_select_related = ("recipient__user", "related_borrow_record", "created_by")


@admin.register(EmailReminder)
class EmailReminderAdmin(ReadOnlyDeliveryAdmin):
    list_display = (
        "email_to",
        "subject",
        "member",
        "reminder_type",
        "attempt_number",
        "status",
        "attempted_at",
    )
    list_filter = ("reminder_type", "status", "attempted_at")
    search_fields = ("email_to", "subject", "member__member_code", "message")
    list_select_related = ("notification", "member__user", "borrow_record")

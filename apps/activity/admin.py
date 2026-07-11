from django.contrib import admin

from .models import ActivityLog, AuditLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "module", "method", "status_code", "ip_address", "created_at")
    list_filter = ("module", "method", "status_code", "created_at")
    search_fields = ("user__username", "action", "description", "path", "ip_address")
    readonly_fields = ("user", "action", "module", "description", "method", "path", "status_code", "ip_address", "user_agent", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "model_name", "object_id", "ip_address", "created_at")
    list_filter = ("action_type", "app_label", "model_name", "created_at")
    search_fields = ("user__username", "model_name", "object_id", "object_repr")
    readonly_fields = ("user", "app_label", "model_name", "object_id", "object_repr", "action_type", "old_values", "new_values", "ip_address", "created_at")

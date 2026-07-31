from django.contrib import admin

from .models import BackupRecord, BackupSchedule, LibraryProfile, SystemSetting


@admin.register(LibraryProfile)
class LibraryProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "theme", "updated_at")


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "updated_at")
    search_fields = ("key", "value", "description")


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ("frequency", "backup_time", "is_enabled", "backup_directory", "updated_at")


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ("file_name", "file_size", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("file_name", "message")
    readonly_fields = ("file_name", "file_path", "file_size", "status", "message", "created_by", "created_at")

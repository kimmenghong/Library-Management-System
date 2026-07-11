from django.contrib import admin

from .models import ExportJob, ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ("target", "status", "total_rows", "success_rows", "failed_rows", "created_by", "created_at")
    list_filter = ("target", "status", "created_at")
    search_fields = ("message",)
    autocomplete_fields = ("created_by",)


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ("target", "file_format", "created_by", "created_at")
    list_filter = ("target", "file_format", "created_at")
    autocomplete_fields = ("created_by",)

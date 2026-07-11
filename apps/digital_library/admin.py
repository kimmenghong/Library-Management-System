from django.contrib import admin

from .models import DigitalBook, DigitalBookCategory


@admin.register(DigitalBookCategory)
class DigitalBookCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name", "description")
    list_filter = ("is_active",)


@admin.register(DigitalBook)
class DigitalBookAdmin(admin.ModelAdmin):
    list_display = ("title", "file_type", "category", "is_public", "is_active", "download_count")
    list_filter = ("file_type", "category", "is_public", "is_active")
    search_fields = ("title", "description", "book__title")
    filter_horizontal = ("allowed_roles",)
    autocomplete_fields = ("book", "uploaded_by")

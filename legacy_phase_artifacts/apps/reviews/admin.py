from django.contrib import admin

from .models import BookReview


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "member", "rating", "status", "created_at")
    list_filter = ("rating", "status", "created_at")
    search_fields = ("book__title", "member__member_code", "review_text")
    autocomplete_fields = ("book", "member", "moderated_by")

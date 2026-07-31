from django.contrib import admin

from .models import FAQ, Feedback, SupportTicket


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "display_order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "user", "status", "priority", "assigned_to", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("subject", "message", "user__username")
    autocomplete_fields = ("user", "assigned_to")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "rating", "is_reviewed", "created_at")
    list_filter = ("rating", "is_reviewed", "created_at")
    search_fields = ("name", "email", "message")

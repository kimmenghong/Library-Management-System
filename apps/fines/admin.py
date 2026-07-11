from django.contrib import admin

from .models import Fine, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = (
        "payment_date",
        "amount_paid",
        "payment_method",
        "reference_number",
        "status",
        "received_by",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class ReadOnlyFinancialAdmin(admin.ModelAdmin):
    """Financial history is changed only through the locked application services."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Fine)
class FineAdmin(ReadOnlyFinancialAdmin):
    list_display = (
        "member",
        "amount",
        "paid_amount",
        "balance",
        "reason",
        "status",
        "created_at",
    )
    list_filter = ("status", "reason", "created_at")
    search_fields = (
        "member__member_code",
        "member__user__username",
        "borrow_record__book_copy__copy_code",
        "description",
    )
    list_select_related = ("member__user", "borrow_record", "created_by", "waived_by")
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(ReadOnlyFinancialAdmin):
    list_display = (
        "fine",
        "member",
        "amount_paid",
        "payment_method",
        "payment_date",
        "status",
        "received_by",
    )
    list_filter = ("status", "payment_method", "payment_date")
    search_fields = (
        "member__member_code",
        "reference_number",
        "fine__description",
    )
    list_select_related = ("fine", "member__user", "received_by", "voided_by")

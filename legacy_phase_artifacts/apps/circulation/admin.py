from django.contrib import admin

from .models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord


@admin.register(BorrowingPolicy)
class BorrowingPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "member_type",
        "max_books",
        "loan_period_days",
        "renewal_days",
        "max_renewals",
        "fine_per_day",
        "reservation_expiry_days",
        "is_active",
    )
    list_filter = ("member_type", "is_active")
    readonly_fields = ("created_at", "updated_at")


class ImmutableTransactionAdmin(admin.ModelAdmin):
    """Circulation transactions must be changed through atomic service workflows."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BorrowRecord)
class BorrowRecordAdmin(ImmutableTransactionAdmin):
    list_display = (
        "member",
        "book_copy",
        "borrow_date",
        "due_date",
        "return_date",
        "status",
        "renewal_count",
        "fine_rate_per_day",
    )
    list_filter = ("status", "borrow_date", "due_date")
    search_fields = (
        "member__member_code",
        "member__user__username",
        "book_copy__copy_code",
        "book_copy__barcode",
        "book_copy__book__title",
    )
    list_select_related = ("member__user", "book_copy__book", "borrowed_by")
    date_hierarchy = "borrow_date"


@admin.register(ReturnRecord)
class ReturnRecordAdmin(ImmutableTransactionAdmin):
    list_display = (
        "borrow_record",
        "return_date",
        "book_condition",
        "fine_amount",
        "returned_by",
    )
    list_filter = ("book_condition", "return_date")
    search_fields = (
        "borrow_record__member__member_code",
        "borrow_record__book_copy__copy_code",
    )
    list_select_related = (
        "borrow_record__member__user",
        "borrow_record__book_copy__book",
        "returned_by",
    )
    date_hierarchy = "return_date"


@admin.register(RenewalRecord)
class RenewalRecordAdmin(ImmutableTransactionAdmin):
    list_display = (
        "borrow_record",
        "old_due_date",
        "new_due_date",
        "renewed_by",
        "created_at",
    )
    search_fields = (
        "borrow_record__member__member_code",
        "borrow_record__book_copy__copy_code",
    )
    list_select_related = (
        "borrow_record__member__user",
        "borrow_record__book_copy__book",
        "renewed_by",
    )


@admin.register(Reservation)
class ReservationAdmin(ImmutableTransactionAdmin):
    list_display = (
        "member",
        "book",
        "reserved_date",
        "ready_date",
        "expiry_date",
        "status",
    )
    list_filter = ("status", "reserved_date", "ready_date", "expiry_date")
    search_fields = (
        "member__member_code",
        "member__user__username",
        "book__title",
        "book__book_code",
    )
    list_select_related = ("member__user", "book")

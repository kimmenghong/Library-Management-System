from django.contrib import admin

from .models import BookStatusLog, DamagedBook, LostBook, RepairRecord
from .services import (
    create_repair_record,
    report_damaged_book,
    report_lost_book,
    update_damaged_record,
    update_lost_record,
    update_repair_status,
)


@admin.register(BookStatusLog)
class BookStatusLogAdmin(admin.ModelAdmin):
    list_display = ("book_copy", "previous_status", "new_status", "reason", "changed_by", "created_at")
    list_filter = ("new_status", "reason", "created_at")
    search_fields = ("book_copy__copy_code", "book__title", "reason", "notes")
    autocomplete_fields = ("book", "book_copy", "changed_by")
    readonly_fields = (
        "book",
        "book_copy",
        "previous_status",
        "new_status",
        "reason",
        "notes",
        "changed_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LostBook)
class LostBookAdmin(admin.ModelAdmin):
    list_display = ("book_copy", "member", "reported_date", "replacement_cost", "status")
    list_filter = ("status", "reported_date", "resolved_date")
    search_fields = ("book_copy__copy_code", "book_copy__book__title", "member__member_code")
    autocomplete_fields = ("book_copy", "borrow_record", "member", "reported_by")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if change:
            update_lost_record(
                obj,
                status=obj.status,
                replacement_cost=obj.replacement_cost,
                description=obj.description,
                resolution_notes=obj.resolution_notes,
                resolved_date=obj.resolved_date,
                changed_by=request.user,
            )
            return
        record = report_lost_book(
            obj.book_copy,
            reported_by=obj.reported_by or request.user,
            borrow_record=obj.borrow_record,
            member=obj.member,
            replacement_cost=obj.replacement_cost,
            description=obj.description,
        )
        obj.pk = record.pk


@admin.register(DamagedBook)
class DamagedBookAdmin(admin.ModelAdmin):
    list_display = ("book_copy", "member", "reported_date", "severity", "estimated_repair_cost", "status")
    list_filter = ("status", "severity", "reported_date", "resolved_date")
    search_fields = ("book_copy__copy_code", "book_copy__book__title", "member__member_code")
    autocomplete_fields = ("book_copy", "borrow_record", "member", "reported_by")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if change:
            update_damaged_record(
                obj,
                status=obj.status,
                severity=obj.severity,
                estimated_repair_cost=obj.estimated_repair_cost,
                description=obj.description,
                resolution_notes=obj.resolution_notes,
                resolved_date=obj.resolved_date,
                changed_by=request.user,
            )
            return
        record = report_damaged_book(
            obj.book_copy,
            reported_by=obj.reported_by or request.user,
            borrow_record=obj.borrow_record,
            member=obj.member,
            severity=obj.severity,
            estimated_repair_cost=obj.estimated_repair_cost,
            description=obj.description,
        )
        obj.pk = record.pk


@admin.register(RepairRecord)
class RepairRecordAdmin(admin.ModelAdmin):
    list_display = ("book_copy", "vendor", "sent_date", "expected_return_date", "completed_date", "repair_cost", "status")
    list_filter = ("status", "sent_date", "completed_date")
    search_fields = ("book_copy__copy_code", "book_copy__book__title", "vendor", "notes")
    autocomplete_fields = ("book_copy", "damage_record", "sent_by")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if change:
            update_repair_status(
                obj,
                status=obj.status,
                changed_by=request.user,
                completed_date=obj.completed_date,
                notes=obj.notes,
                vendor=obj.vendor,
                expected_return_date=obj.expected_return_date,
                repair_cost=obj.repair_cost,
            )
            return
        record = create_repair_record(
            obj.book_copy,
            sent_by=obj.sent_by or request.user,
            damage_record=obj.damage_record,
            vendor=obj.vendor,
            expected_return_date=obj.expected_return_date,
            repair_cost=obj.repair_cost,
            notes=obj.notes,
        )
        obj.pk = record.pk

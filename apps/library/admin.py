from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import (
    Author,
    Book,
    BorrowRecord,
    Category,
    Fine,
    Member,
    Notification,
    Publisher,
    Report,
    Role,
    User,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_id", "role_name", "description")
    search_fields = ("role_name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    model = User
    ordering = ("username",)
    list_display = (
        "user_id",
        "username",
        "full_name",
        "email",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "full_name", "email")
    readonly_fields = ("created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal information",
            {"fields": ("full_name", "email", "phone", "address", "role")},
        ),
        (
            "Access",
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "role",
                    "username",
                    "email",
                    "full_name",
                    "phone",
                    "address",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    filter_horizontal = ()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "category_name")
    search_fields = ("category_name",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("author_id", "author_name")
    search_fields = ("author_name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("publisher_id", "publisher_name", "contact_number", "email")
    search_fields = ("publisher_name", "email")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "book_id",
        "title",
        "isbn",
        "author",
        "category",
        "quantity",
        "available_quantity",
        "status",
    )
    list_filter = ("status", "category", "publisher", "publication_year")
    search_fields = ("title", "isbn", "author__author_name")
    list_select_related = ("author", "category", "publisher")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "member_id",
        "member_code",
        "user",
        "member_type",
        "department",
        "status",
    )
    list_filter = ("member_type", "status")
    search_fields = ("member_code", "user__username", "user__full_name")
    list_select_related = ("user",)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = (
        "borrow_id",
        "member",
        "book",
        "borrow_date",
        "due_date",
        "return_date",
        "status",
        "issued_by",
        "received_by",
    )
    list_filter = ("status", "borrow_date", "due_date")
    search_fields = ("member__member_code", "book__title", "book__isbn")
    list_select_related = ("member__user", "book", "issued_by", "received_by")


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = (
        "fine_id",
        "borrow",
        "member",
        "amount",
        "paid_amount",
        "balance",
        "status",
        "paid_date",
    )
    list_filter = ("status", "created_at")
    search_fields = ("member__member_code", "borrow__book__title")
    list_select_related = ("borrow__book", "member__user")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "notification_id",
        "member",
        "title",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("member__member_code", "title", "message")
    list_select_related = ("member__user",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "report_id",
        "report_type",
        "generated_by",
        "generated_at",
        "file_path",
    )
    list_filter = ("report_type", "generated_at")
    search_fields = ("generated_by__username",)
    list_select_related = ("generated_by",)


admin.site.site_header = "Library Management Administration"
admin.site.site_title = "Library Management"
admin.site.index_title = "Lecturer Data Dictionary"

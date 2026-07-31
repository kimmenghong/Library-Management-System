from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Permission, Role, User


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "module", "action", "is_active")
    list_filter = ("module", "action", "is_active")
    search_fields = ("name", "codename", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "is_active", "created_at")
    list_filter = ("is_system", "is_active")
    search_fields = ("name", "slug", "description")
    filter_horizontal = ("permissions",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system:
            fields.extend(["slug", "is_system"])
        return fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("username",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Library System Profile",
            {
                "fields": (
                    "role",
                    "phone",
                    "address",
                    "avatar",
                    "must_change_password",
                    "created_by",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "Library System Profile",
            {
                "classes": ("wide",),
                "fields": ("email", "role", "phone", "address", "is_staff", "is_active"),
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        if obj and (obj == request.user or (obj.is_superuser and not request.user.is_superuser)):
            return False
        return super().has_delete_permission(request, obj)

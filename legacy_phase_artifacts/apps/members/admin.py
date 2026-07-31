from django.contrib import admin

from .models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile


class ProfileInlineBase(admin.StackedInline):
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ("created_at", "updated_at")


class StudentProfileInline(ProfileInlineBase):
    model = StudentProfile


class TeacherProfileInline(ProfileInlineBase):
    model = TeacherProfile


class StaffProfileInline(ProfileInlineBase):
    model = StaffProfile


class LibrarianProfileInline(ProfileInlineBase):
    model = LibrarianProfile


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "member_code",
        "display_name",
        "member_type",
        "status",
        "joined_date",
        "expiry_date",
    )
    list_filter = ("member_type", "status", "joined_date", "expiry_date")
    search_fields = (
        "member_code",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone",
    )
    autocomplete_fields = ("user",)
    list_select_related = ("user", "user__role")
    readonly_fields = ("member_code", "created_at", "updated_at")
    date_hierarchy = "joined_date"

    def get_inlines(self, request, obj):
        if not obj:
            return []
        inline_map = {
            Member.STUDENT: StudentProfileInline,
            Member.TEACHER: TeacherProfileInline,
            Member.STAFF: StaffProfileInline,
            Member.LIBRARIAN: LibrarianProfileInline,
            Member.ASSISTANT_LIBRARIAN: LibrarianProfileInline,
        }
        return [inline_map[obj.member_type]]


class SpecializedProfileAdmin(admin.ModelAdmin):
    autocomplete_fields = ("member",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("member", "member__user")


@admin.register(StudentProfile)
class StudentProfileAdmin(SpecializedProfileAdmin):
    list_display = ("student_id", "member", "department", "year_level", "semester")
    search_fields = (
        "student_id",
        "member__member_code",
        "member__user__username",
        "member__user__email",
    )
    list_filter = ("department", "year_level", "semester")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(SpecializedProfileAdmin):
    list_display = ("teacher_id", "member", "faculty", "department", "designation")
    search_fields = (
        "teacher_id",
        "member__member_code",
        "member__user__username",
        "member__user__email",
    )
    list_filter = ("faculty", "department")


@admin.register(StaffProfile)
class StaffProfileAdmin(SpecializedProfileAdmin):
    list_display = ("staff_id", "member", "department", "position")
    search_fields = (
        "staff_id",
        "member__member_code",
        "member__user__username",
        "member__user__email",
    )
    list_filter = ("department", "position")


@admin.register(LibrarianProfile)
class LibrarianProfileAdmin(SpecializedProfileAdmin):
    list_display = (
        "librarian_id",
        "member",
        "employee_type",
        "department",
        "shift",
        "can_approve_overrides",
    )
    search_fields = (
        "librarian_id",
        "member__member_code",
        "member__user__username",
        "member__user__email",
    )
    list_filter = ("employee_type", "department", "can_approve_overrides")

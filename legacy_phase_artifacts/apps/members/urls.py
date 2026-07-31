from django.urls import path

from . import views


app_name = "members"

urlpatterns = [
    path("", views.MemberListView.as_view(), name="member_list"),
    path("create/", views.MemberCreateView.as_view(), name="member_create"),
    path("<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member_update"),
    path(
        "<int:pk>/status/",
        views.MemberStatusUpdateView.as_view(),
        name="member_status_update",
    ),
    path(
        "student-profiles/create/",
        views.StudentProfileCreateView.as_view(),
        name="student_profile_create",
    ),
    path(
        "<int:member_pk>/student-profile/create/",
        views.StudentProfileCreateView.as_view(),
        name="student_profile_create_for_member",
    ),
    path(
        "student-profiles/<int:pk>/edit/",
        views.StudentProfileUpdateView.as_view(),
        name="student_profile_update",
    ),
    path(
        "teacher-profiles/create/",
        views.TeacherProfileCreateView.as_view(),
        name="teacher_profile_create",
    ),
    path(
        "<int:member_pk>/teacher-profile/create/",
        views.TeacherProfileCreateView.as_view(),
        name="teacher_profile_create_for_member",
    ),
    path(
        "teacher-profiles/<int:pk>/edit/",
        views.TeacherProfileUpdateView.as_view(),
        name="teacher_profile_update",
    ),
    path(
        "staff-profiles/create/",
        views.StaffProfileCreateView.as_view(),
        name="staff_profile_create",
    ),
    path(
        "<int:member_pk>/staff-profile/create/",
        views.StaffProfileCreateView.as_view(),
        name="staff_profile_create_for_member",
    ),
    path(
        "staff-profiles/<int:pk>/edit/",
        views.StaffProfileUpdateView.as_view(),
        name="staff_profile_update",
    ),
    path(
        "librarian-profiles/create/",
        views.LibrarianProfileCreateView.as_view(),
        name="librarian_profile_create",
    ),
    path(
        "<int:member_pk>/librarian-profile/create/",
        views.LibrarianProfileCreateView.as_view(),
        name="librarian_profile_create_for_member",
    ),
    path(
        "librarian-profiles/<int:pk>/edit/",
        views.LibrarianProfileUpdateView.as_view(),
        name="librarian_profile_update",
    ),
]

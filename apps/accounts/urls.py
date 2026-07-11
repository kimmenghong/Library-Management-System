from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-change/",
        views.AccountPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-reset/",
        views.AccountPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.AccountPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path(
        "users/<int:pk>/toggle-status/",
        views.UserStatusToggleView.as_view(),
        name="user_toggle_status",
    ),
    path("roles/", views.RoleListView.as_view(), name="role_list"),
    path("roles/create/", views.RoleCreateView.as_view(), name="role_create"),
    path("roles/<int:pk>/edit/", views.RoleUpdateView.as_view(), name="role_update"),
    path("permissions/", views.PermissionListView.as_view(), name="permission_list"),
    path(
        "permissions/create/",
        views.PermissionCreateView.as_view(),
        name="permission_create",
    ),
    path(
        "permissions/<int:pk>/edit/",
        views.PermissionUpdateView.as_view(),
        name="permission_update",
    ),
]

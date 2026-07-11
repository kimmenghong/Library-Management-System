from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    PROTECTED_ROLE_SLUGS,
    AccountAuthenticationForm,
    AccountPasswordChangeForm,
    AccountPasswordResetForm,
    AccountSetPasswordForm,
    PermissionForm,
    ProfileUpdateForm,
    RoleForm,
    UserCreateForm,
    UserUpdateForm,
)
from .mixins import RolePermissionRequiredMixin
from .models import Permission, Role, User


def landing_url_for(user):
    """Return the first useful page the authenticated user may access."""
    if user.has_role_permission("dashboard.view_dashboard"):
        return reverse("dashboard:home")
    if user.has_role_permission("catalog.view_book"):
        return reverse("catalog:book_list")
    if user.has_role_permission("digital.view_digital_book"):
        return reverse("digital_library:list")
    return reverse("accounts:profile")


class AccountLoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = AccountAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.must_change_password:
            return reverse("accounts:password_change")
        return self.get_redirect_url() or landing_url_for(self.request.user)


class AccountPasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    form_class = AccountPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class AccountPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    form_class = AccountSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class AccountPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "registration/password_change_form.html"
    form_class = AccountPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return redirect(landing_url_for(request.user))


class UserListView(RolePermissionRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    permission_codename = "accounts.view_user"

    def get_queryset(self):
        queryset = User.objects.select_related("role").order_by("username")
        query = self.request.GET.get("q", "").strip()
        role = self.request.GET.get("role", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        if role.isdigit():
            queryset = queryset.filter(role_id=role)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = Role.objects.filter(is_active=True).order_by("name")
        return context


class UserDetailView(RolePermissionRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "managed_user"
    permission_codename = "accounts.view_user"

    def get_queryset(self):
        return User.objects.select_related("role")


class UserCreateView(RolePermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    permission_codename = "accounts.add_user"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "User account created successfully.")
        return super().form_valid(form)


class ProtectedUserWriteMixin:
    """Prevent delegated administrators from modifying privileged accounts."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.exclude(
            Q(is_superuser=True) | Q(role__slug__in=PROTECTED_ROLE_SLUGS)
        )


class UserUpdateView(ProtectedUserWriteMixin, RolePermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    permission_codename = "accounts.edit_user"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "User account updated successfully.")
        return super().form_valid(form)


class UserStatusToggleView(RolePermissionRequiredMixin, View):
    permission_codename = "accounts.delete_user"

    def post(self, request, pk):
        target = get_object_or_404(User.objects.select_related("role"), pk=pk)
        if target == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("accounts:user_detail", pk=target.pk)
        if not request.user.is_superuser and (
            target.is_superuser
            or (target.role and target.role.slug in PROTECTED_ROLE_SLUGS)
        ):
            messages.error(request, "Only a superuser can change this account's status.")
            return redirect("accounts:user_detail", pk=target.pk)

        target.is_active = not target.is_active
        target.save(update_fields=["is_active", "updated_at"])
        state = "activated" if target.is_active else "deactivated"
        messages.success(request, f"User account {state} successfully.")
        return redirect("accounts:user_detail", pk=target.pk)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form)


class RoleListView(RolePermissionRequiredMixin, ListView):
    model = Role
    template_name = "accounts/role_list.html"
    context_object_name = "roles"
    paginate_by = 25
    permission_codename = "accounts.view_role"

    def get_queryset(self):
        return Role.objects.prefetch_related("permissions").order_by("name")


class RoleCreateView(RolePermissionRequiredMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role_list")
    permission_codename = "accounts.add_role"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Role created successfully.")
        return super().form_valid(form)


class RoleUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role_list")
    permission_codename = "accounts.edit_role"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_system=False)
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Role updated successfully.")
        return super().form_valid(form)


class PermissionListView(RolePermissionRequiredMixin, ListView):
    model = Permission
    template_name = "accounts/permission_list.html"
    context_object_name = "permissions"
    paginate_by = 30
    permission_codename = "accounts.view_permission"


class PermissionCreateView(RolePermissionRequiredMixin, CreateView):
    model = Permission
    form_class = PermissionForm
    template_name = "accounts/permission_form.html"
    success_url = reverse_lazy("accounts:permission_list")
    permission_codename = "accounts.add_permission"

    def form_valid(self, form):
        messages.success(self.request, "Permission created successfully.")
        return super().form_valid(form)


class PermissionUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Permission
    form_class = PermissionForm
    template_name = "accounts/permission_form.html"
    success_url = reverse_lazy("accounts:permission_list")
    permission_codename = "accounts.edit_permission"

    def form_valid(self, form):
        messages.success(self.request, "Permission updated successfully.")
        return super().form_valid(form)

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class RolePermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    permission_codename = None
    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.permission_codename and user.has_role_permission(self.permission_codename):
            return True
        if self.allowed_roles and user.has_role(*self.allowed_roles):
            return True
        return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect("accounts:dashboard")

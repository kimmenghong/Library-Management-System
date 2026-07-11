from django.views.generic import TemplateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .services import build_dashboard_context


class AnalyticsDashboardView(RolePermissionRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    permission_codename = "dashboard.view_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_dashboard_context(self.request.user))
        return context

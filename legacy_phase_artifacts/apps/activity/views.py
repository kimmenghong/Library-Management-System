from django.db.models import Q
from django.views.generic import DetailView, ListView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .models import ActivityLog, AuditLog


class ActivityLogListView(RolePermissionRequiredMixin, ListView):
    model = ActivityLog
    template_name = "activity/activity_log_list.html"
    context_object_name = "activity_logs"
    paginate_by = 30
    permission_codename = "activity.view_activity"

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related("user")
        query = self.request.GET.get("q")
        module = self.request.GET.get("module")
        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query)
                | Q(action__icontains=query)
                | Q(description__icontains=query)
                | Q(path__icontains=query)
            )
        if module:
            queryset = queryset.filter(module=module)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["modules"] = ActivityLog.objects.exclude(module="").values_list("module", flat=True).distinct().order_by("module")
        return context


class AuditLogListView(RolePermissionRequiredMixin, ListView):
    model = AuditLog
    template_name = "activity/audit_log_list.html"
    context_object_name = "audit_logs"
    paginate_by = 30
    permission_codename = "activity.view_audit"

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user")
        query = self.request.GET.get("q")
        action = self.request.GET.get("action")
        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query)
                | Q(model_name__icontains=query)
                | Q(object_id__icontains=query)
                | Q(object_repr__icontains=query)
            )
        if action:
            queryset = queryset.filter(action_type=action)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = AuditLog.ACTION_CHOICES
        return context


class AuditLogDetailView(RolePermissionRequiredMixin, DetailView):
    model = AuditLog
    template_name = "activity/audit_log_detail.html"
    context_object_name = "audit_log"
    permission_codename = "activity.view_audit"

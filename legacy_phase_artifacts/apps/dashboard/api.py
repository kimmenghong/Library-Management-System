from django.utils import timezone
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import chart_payload, dashboard_metrics


class CanViewDashboard(BasePermission):
    message = "You do not have permission to view dashboard analytics."

    def has_permission(self, request, view):
        return request.user.has_role_permission("dashboard.view_dashboard")


class DashboardAPIView(APIView):
    """Read-only operational metrics for integrations and custom clients."""

    permission_classes = [IsAuthenticated, CanViewDashboard]

    def get(self, request):
        today = timezone.localdate()
        return Response(
            {
                "generated_at": timezone.now().isoformat(),
                "metrics": dashboard_metrics(today=today),
                "charts": chart_payload(today=today),
            }
        )

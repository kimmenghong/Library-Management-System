from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.dashboard.api import DashboardAPIView

from .views import LibraryTokenObtainPairView, api_overview, router


app_name = "api"

urlpatterns = [
    path("", api_overview, name="overview"),
    path("auth/token/", LibraryTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]

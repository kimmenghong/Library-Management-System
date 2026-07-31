from django.urls import path

from . import views


app_name = "dashboard"

urlpatterns = [
    path("", views.AnalyticsDashboardView.as_view(), name="home"),
]

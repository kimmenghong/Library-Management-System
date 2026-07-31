from django.urls import path

from . import views


app_name = "activity"

urlpatterns = [
    path("", views.ActivityLogListView.as_view(), name="activity_log_list"),
    path("audit/", views.AuditLogListView.as_view(), name="audit_log_list"),
    path("audit/<int:pk>/", views.AuditLogDetailView.as_view(), name="audit_log_detail"),
]

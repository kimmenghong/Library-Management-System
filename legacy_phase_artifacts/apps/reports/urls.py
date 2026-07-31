from django.urls import path

from . import views


app_name = "reports"

urlpatterns = [
    path("", views.ReportIndexView.as_view(), name="report_index"),
    path("most-borrowed/", views.MostBorrowedBooksReportView.as_view(), name="most_borrowed"),
    path("active-borrowers/", views.ActiveBorrowersReportView.as_view(), name="active_borrowers"),
    path("members-with-fines/", views.MembersWithFinesReportView.as_view(), name="members_with_fines"),
    path("status/", views.StatusReportView.as_view(), name="status_report"),
    path("export/<slug:report_type>/<str:file_format>/", views.ReportExportView.as_view(), name="report_export"),
]

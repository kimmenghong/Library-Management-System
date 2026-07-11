from django.http import Http404
from django.views.generic import TemplateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .services import (
    REPORT_TITLES,
    active_borrowers,
    export_excel,
    export_pdf,
    members_with_fines,
    most_borrowed_books,
    status_report,
)


class ReportIndexView(RolePermissionRequiredMixin, TemplateView):
    template_name = "reports/report_index.html"
    permission_codename = "reports.view_report"


class MostBorrowedBooksReportView(RolePermissionRequiredMixin, TemplateView):
    template_name = "reports/most_borrowed.html"
    permission_codename = "reports.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["books"] = most_borrowed_books()
        context["report_type"] = "most-borrowed"
        return context


class ActiveBorrowersReportView(RolePermissionRequiredMixin, TemplateView):
    template_name = "reports/active_borrowers.html"
    permission_codename = "reports.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = active_borrowers()
        context["report_type"] = "active-borrowers"
        return context


class MembersWithFinesReportView(RolePermissionRequiredMixin, TemplateView):
    template_name = "reports/members_with_fines.html"
    permission_codename = "reports.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = members_with_fines()
        context["report_type"] = "members-with-fines"
        return context


class StatusReportView(RolePermissionRequiredMixin, TemplateView):
    template_name = "reports/status_report.html"
    permission_codename = "reports.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(status_report())
        context["report_type"] = "status"
        return context


class ReportExportView(RolePermissionRequiredMixin, TemplateView):
    permission_codename = "reports.export_report"

    def get(self, request, *args, **kwargs):
        report_type = kwargs["report_type"]
        file_format = kwargs["file_format"]
        if report_type not in REPORT_TITLES:
            raise Http404("Unknown report type.")
        if file_format == "pdf":
            return export_pdf(report_type)
        if file_format == "excel":
            return export_excel(report_type)
        raise Http404("Unknown export format.")

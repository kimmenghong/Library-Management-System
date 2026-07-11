from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import BookImportForm, ExportForm
from .models import ExportJob, ImportJob
from .services import export_dataset, import_books_from_job


class ImportExportHomeView(RolePermissionRequiredMixin, ListView):
    model = ImportJob
    template_name = "import_export/home.html"
    context_object_name = "import_jobs"
    permission_codename = "import_export.view_import_export"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_jobs"] = ExportJob.objects.select_related("created_by")[:10]
        return context


class BookImportView(RolePermissionRequiredMixin, FormView):
    template_name = "import_export/book_import_form.html"
    form_class = BookImportForm
    success_url = reverse_lazy("import_export:home")
    permission_codename = "import_export.import_data"

    def form_valid(self, form):
        job = form.save(commit=False)
        job.created_by = self.request.user
        job.save()
        import_books_from_job(job)
        messages.success(self.request, job.message)
        return super().form_valid(form)


class ExportDataView(RolePermissionRequiredMixin, FormView):
    template_name = "import_export/export_form.html"
    form_class = ExportForm
    permission_codename = "import_export.export_data"

    def form_valid(self, form):
        ExportJob.objects.create(
            target=form.cleaned_data["target"],
            file_format=form.cleaned_data["file_format"],
            created_by=self.request.user,
        )
        return export_dataset(form.cleaned_data["target"], form.cleaned_data["file_format"])

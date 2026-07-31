from django.urls import path

from . import views


app_name = "import_export"

urlpatterns = [
    path("", views.ImportExportHomeView.as_view(), name="home"),
    path("books/import/", views.BookImportView.as_view(), name="book_import"),
    path("export/", views.ExportDataView.as_view(), name="export"),
]

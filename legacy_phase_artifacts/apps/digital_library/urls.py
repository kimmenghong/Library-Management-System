from django.urls import path

from . import views


app_name = "digital_library"

urlpatterns = [
    path("", views.DigitalBookListView.as_view(), name="list"),
    path("upload/", views.DigitalBookCreateView.as_view(), name="create"),
    path("<int:pk>/", views.DigitalBookDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.DigitalBookUpdateView.as_view(), name="update"),
    path("<int:pk>/download/", views.DigitalBookDownloadView.as_view(), name="download"),
    path("categories/", views.DigitalCategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.DigitalCategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.DigitalCategoryUpdateView.as_view(), name="category_update"),
]

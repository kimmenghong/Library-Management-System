from django.urls import path

from . import views


app_name = "catalog"

urlpatterns = [
    path("", views.BookListView.as_view(), name="book_list"),
    path("books/create/", views.BookCreateView.as_view(), name="book_create"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_update"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("authors/", views.AuthorListView.as_view(), name="author_list"),
    path("authors/create/", views.AuthorCreateView.as_view(), name="author_create"),
    path("authors/<int:pk>/edit/", views.AuthorUpdateView.as_view(), name="author_update"),
    path("authors/<int:pk>/delete/", views.AuthorDeleteView.as_view(), name="author_delete"),
    path("publishers/", views.PublisherListView.as_view(), name="publisher_list"),
    path("publishers/create/", views.PublisherCreateView.as_view(), name="publisher_create"),
    path("publishers/<int:pk>/edit/", views.PublisherUpdateView.as_view(), name="publisher_update"),
    path("publishers/<int:pk>/delete/", views.PublisherDeleteView.as_view(), name="publisher_delete"),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    path("shelves/", views.ShelfListView.as_view(), name="shelf_list"),
    path("shelves/create/", views.ShelfCreateView.as_view(), name="shelf_create"),
    path("shelves/<int:pk>/edit/", views.ShelfUpdateView.as_view(), name="shelf_update"),
    path("shelves/<int:pk>/delete/", views.ShelfDeleteView.as_view(), name="shelf_delete"),
    path("locations/", views.LocationListView.as_view(), name="location_list"),
    path("locations/create/", views.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    path("locations/<int:pk>/delete/", views.LocationDeleteView.as_view(), name="location_delete"),
    path("copies/", views.BookCopyListView.as_view(), name="bookcopy_list"),
    path("copies/create/", views.BookCopyCreateView.as_view(), name="bookcopy_create"),
    path("copies/<int:pk>/qr/", views.BookCopyQRCodeView.as_view(), name="bookcopy_qr"),
    path("copies/<int:pk>/edit/", views.BookCopyUpdateView.as_view(), name="bookcopy_update"),
    path("copies/<int:pk>/delete/", views.BookCopyDeleteView.as_view(), name="bookcopy_delete"),
]

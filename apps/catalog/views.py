from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Prefetch, Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import (
    AdvancedBookSearchForm,
    AuthorForm,
    BookCopyForm,
    BookForm,
    BookLocationForm,
    CategoryForm,
    PublisherForm,
    ShelfForm,
)
from .models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf
from .services import generate_qr_svg


class CatalogFormMessageMixin:
    success_message = "Record saved successfully."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class BookListView(RolePermissionRequiredMixin, ListView):
    model = Book
    template_name = "catalog/book_list.html"
    context_object_name = "books"
    paginate_by = 20
    permission_codename = "catalog.view_book"

    def get_search_form(self):
        if not hasattr(self, "_search_form"):
            self._search_form = AdvancedBookSearchForm(self.request.GET or None)
        return self._search_form

    def get_queryset(self):
        queryset = (
            Book.objects.select_related("publisher", "category")
            .prefetch_related("authors")
            .annotate(
                copy_count=Count("copies", distinct=True),
                available_count=Count(
                    "copies",
                    filter=Q(copies__status=BookCopy.AVAILABLE),
                    distinct=True,
                ),
            )
            .order_by("title")
        )
        form = self.get_search_form()
        if not self.request.GET:
            return queryset
        if not form.is_valid():
            return queryset.none()

        filters = form.cleaned_data
        for term in filters.get("q", "").strip().split():
            queryset = queryset.filter(
                Q(title__icontains=term)
                | Q(subtitle__icontains=term)
                | Q(isbn__icontains=term)
                | Q(book_code__icontains=term)
                | Q(authors__name__icontains=term)
                | Q(publisher__name__icontains=term)
                | Q(category__name__icontains=term)
                | Q(copies__barcode__icontains=term)
                | Q(copies__copy_code__icontains=term)
            )
        if filters.get("title"):
            queryset = queryset.filter(
                Q(title__icontains=filters["title"])
                | Q(subtitle__icontains=filters["title"])
            )
        if filters.get("isbn"):
            queryset = queryset.filter(isbn__icontains=filters["isbn"])
        if filters.get("book_code"):
            queryset = queryset.filter(book_code__icontains=filters["book_code"])
        if filters.get("barcode"):
            queryset = queryset.filter(copies__barcode__icontains=filters["barcode"])
        if filters.get("author"):
            queryset = queryset.filter(authors=filters["author"])
        if filters.get("publisher"):
            queryset = queryset.filter(publisher=filters["publisher"])
        if filters.get("category"):
            queryset = queryset.filter(category=filters["category"])
        if filters.get("shelf"):
            queryset = queryset.filter(
                Q(copies__shelf=filters["shelf"])
                | Q(copies__location__shelf=filters["shelf"])
            )
        if filters.get("availability"):
            queryset = queryset.filter(copies__status=filters["availability"])
        if filters.get("publication_year"):
            queryset = queryset.filter(publication_year=filters["publication_year"])
        if filters.get("language"):
            queryset = queryset.filter(language__icontains=filters["language"])
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["advanced_form"] = self.get_search_form()
        context["summary"] = {
            "titles": Book.objects.count(),
            "copies": BookCopy.objects.count(),
            "available": BookCopy.objects.filter(status=BookCopy.AVAILABLE).count(),
            "borrowed": BookCopy.objects.filter(status=BookCopy.BORROWED).count(),
        }
        return context


class BookDetailView(RolePermissionRequiredMixin, DetailView):
    model = Book
    template_name = "catalog/book_detail.html"
    context_object_name = "book"
    permission_codename = "catalog.view_book"

    def get_queryset(self):
        copies = BookCopy.objects.select_related("shelf", "location", "location__shelf")
        return (
            Book.objects.select_related("publisher", "category", "created_by", "updated_by")
            .prefetch_related("authors", Prefetch("copies", queryset=copies))
        )


class BookCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"
    permission_codename = "catalog.add_book"
    success_message = "Book created successfully."

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:book_detail", kwargs={"pk": self.object.pk})


class BookUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"
    permission_codename = "catalog.edit_book"
    success_message = "Book updated successfully."

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:book_detail", kwargs={"pk": self.object.pk})


class SafeCatalogDeleteView(RolePermissionRequiredMixin, DeleteView):
    template_name = "catalog/confirm_delete.html"
    deleted_label = "Record"

    def related_records(self, obj):
        relations = []
        for relation in obj._meta.related_objects:
            accessor = relation.get_accessor_name()
            if not accessor:
                continue
            try:
                related = getattr(obj, accessor)
                exists = bool(related) if relation.one_to_one else related.exists()
            except (AttributeError, ObjectDoesNotExist):
                exists = False
            if exists:
                relations.append(relation.related_model._meta.verbose_name_plural.title())
        return sorted(set(relations))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        related = self.related_records(self.object)
        if related:
            messages.error(
                request,
                f"{self.deleted_label} cannot be deleted because it is referenced by: "
                f"{', '.join(related)}. Deactivate it instead.",
            )
            return redirect(self.success_url)
        try:
            response = super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, f"{self.deleted_label} is protected by historical records.")
            return redirect(self.success_url)
        messages.success(request, f"{self.deleted_label} deleted successfully.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["related_records"] = self.related_records(self.object)
        return context


class BookDeleteView(SafeCatalogDeleteView):
    model = Book
    success_url = reverse_lazy("catalog:book_list")
    permission_codename = "catalog.delete_book"
    deleted_label = "Book"


class ManagedListView(RolePermissionRequiredMixin, ListView):
    paginate_by = 25
    search_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(condition)
        return queryset


class AuthorListView(ManagedListView):
    model = Author
    template_name = "catalog/author_list.html"
    context_object_name = "authors"
    permission_codename = "catalog.manage_author"
    search_fields = ("name", "nationality")

    def get_queryset(self):
        return super().get_queryset().annotate(book_count=Count("books", distinct=True)).order_by("name")


class AuthorCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = "catalog/author_form.html"
    success_url = reverse_lazy("catalog:author_list")
    permission_codename = "catalog.manage_author"
    success_message = "Author created successfully."


class AuthorUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = "catalog/author_form.html"
    success_url = reverse_lazy("catalog:author_list")
    permission_codename = "catalog.manage_author"
    success_message = "Author updated successfully."


class AuthorDeleteView(SafeCatalogDeleteView):
    model = Author
    success_url = reverse_lazy("catalog:author_list")
    permission_codename = "catalog.manage_author"
    deleted_label = "Author"


class PublisherListView(ManagedListView):
    model = Publisher
    template_name = "catalog/publisher_list.html"
    context_object_name = "publishers"
    permission_codename = "catalog.manage_publisher"
    search_fields = ("name", "contact_email")

    def get_queryset(self):
        return super().get_queryset().annotate(book_count=Count("books")).order_by("name")


class PublisherCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = Publisher
    form_class = PublisherForm
    template_name = "catalog/publisher_form.html"
    success_url = reverse_lazy("catalog:publisher_list")
    permission_codename = "catalog.manage_publisher"
    success_message = "Publisher created successfully."


class PublisherUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = Publisher
    form_class = PublisherForm
    template_name = "catalog/publisher_form.html"
    success_url = reverse_lazy("catalog:publisher_list")
    permission_codename = "catalog.manage_publisher"
    success_message = "Publisher updated successfully."


class PublisherDeleteView(SafeCatalogDeleteView):
    model = Publisher
    success_url = reverse_lazy("catalog:publisher_list")
    permission_codename = "catalog.manage_publisher"
    deleted_label = "Publisher"


class CategoryListView(ManagedListView):
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    permission_codename = "catalog.manage_category"
    search_fields = ("name", "code")

    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related("parent")
            .annotate(book_count=Count("books"))
            .order_by("name")
        )


class CategoryCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    permission_codename = "catalog.manage_category"
    success_message = "Category created successfully."


class CategoryUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    permission_codename = "catalog.manage_category"
    success_message = "Category updated successfully."


class CategoryDeleteView(SafeCatalogDeleteView):
    model = Category
    success_url = reverse_lazy("catalog:category_list")
    permission_codename = "catalog.manage_category"
    deleted_label = "Category"


class ShelfListView(ManagedListView):
    model = Shelf
    template_name = "catalog/shelf_list.html"
    context_object_name = "shelves"
    permission_codename = "catalog.manage_location"
    search_fields = ("shelf_code", "name", "section")

    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(
                location_count=Count("locations", distinct=True),
                copy_count=Count("book_copies", distinct=True),
            )
            .order_by("shelf_code")
        )


class ShelfCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = Shelf
    form_class = ShelfForm
    template_name = "catalog/shelf_form.html"
    success_url = reverse_lazy("catalog:shelf_list")
    permission_codename = "catalog.manage_location"
    success_message = "Shelf created successfully."


class ShelfUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = Shelf
    form_class = ShelfForm
    template_name = "catalog/shelf_form.html"
    success_url = reverse_lazy("catalog:shelf_list")
    permission_codename = "catalog.manage_location"
    success_message = "Shelf updated successfully."


class ShelfDeleteView(SafeCatalogDeleteView):
    model = Shelf
    success_url = reverse_lazy("catalog:shelf_list")
    permission_codename = "catalog.manage_location"
    deleted_label = "Shelf"


class LocationListView(ManagedListView):
    model = BookLocation
    template_name = "catalog/location_list.html"
    context_object_name = "locations"
    permission_codename = "catalog.manage_location"
    search_fields = ("label", "shelf__shelf_code", "aisle", "row", "column")

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .select_related("shelf")
            .annotate(copy_count=Count("book_copies"))
            .order_by("shelf__shelf_code", "label")
        )
        shelf = self.request.GET.get("shelf", "")
        if shelf.isdigit():
            queryset = queryset.filter(shelf_id=shelf)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shelves"] = Shelf.objects.filter(is_active=True).order_by("shelf_code")
        return context


class LocationCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = BookLocation
    form_class = BookLocationForm
    template_name = "catalog/location_form.html"
    success_url = reverse_lazy("catalog:location_list")
    permission_codename = "catalog.manage_location"
    success_message = "Book location created successfully."


class LocationUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = BookLocation
    form_class = BookLocationForm
    template_name = "catalog/location_form.html"
    success_url = reverse_lazy("catalog:location_list")
    permission_codename = "catalog.manage_location"
    success_message = "Book location updated successfully."


class LocationDeleteView(SafeCatalogDeleteView):
    model = BookLocation
    success_url = reverse_lazy("catalog:location_list")
    permission_codename = "catalog.manage_location"
    deleted_label = "Book location"


class BookCopyListView(RolePermissionRequiredMixin, ListView):
    model = BookCopy
    template_name = "catalog/bookcopy_list.html"
    context_object_name = "copies"
    paginate_by = 25
    permission_codename = "catalog.manage_copy"

    def get_queryset(self):
        queryset = BookCopy.objects.select_related(
            "book", "shelf", "location", "location__shelf"
        ).order_by("book__title", "copy_code")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if query:
            for term in query.split():
                queryset = queryset.filter(
                    Q(copy_code__icontains=term)
                    | Q(barcode__icontains=term)
                    | Q(book__title__icontains=term)
                    | Q(book__isbn__icontains=term)
                    | Q(book__book_code__icontains=term)
                )
        if status in dict(BookCopy.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = BookCopy.STATUS_CHOICES
        context["summary"] = {
            status: BookCopy.objects.filter(status=status).count()
            for status, _label in BookCopy.STATUS_CHOICES
        }
        return context


class BookCopyCreateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, CreateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = "catalog/bookcopy_form.html"
    permission_codename = "catalog.manage_copy"
    success_message = "Book copy registered successfully."

    def dispatch(self, request, *args, **kwargs):
        self.book = None
        book_id = request.GET.get("book") or request.POST.get("book_context")
        if book_id and str(book_id).isdigit():
            self.book = get_object_or_404(Book, pk=book_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["book"] = self.book
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_book"] = self.book
        return context

    def get_success_url(self):
        return reverse("catalog:book_detail", kwargs={"pk": self.object.book_id})


class BookCopyUpdateView(CatalogFormMessageMixin, RolePermissionRequiredMixin, UpdateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = "catalog/bookcopy_form.html"
    permission_codename = "catalog.manage_copy"
    success_message = "Book copy updated successfully."

    def get_queryset(self):
        return BookCopy.objects.select_related("book", "shelf", "location")

    def get_success_url(self):
        return reverse("catalog:book_detail", kwargs={"pk": self.object.book_id})


class BookCopyDeleteView(SafeCatalogDeleteView):
    model = BookCopy
    success_url = reverse_lazy("catalog:bookcopy_list")
    permission_codename = "catalog.manage_copy"
    deleted_label = "Book copy"


class BookCopyQRCodeView(RolePermissionRequiredMixin, View):
    permission_codename = "catalog.view_book"

    def get(self, request, pk):
        book_copy = get_object_or_404(BookCopy.objects.select_related("book"), pk=pk)
        response = HttpResponse(
            generate_qr_svg(book_copy.qr_payload),
            content_type="image/svg+xml; charset=utf-8",
        )
        disposition = "attachment" if request.GET.get("download") == "1" else "inline"
        response["Content-Disposition"] = (
            f'{disposition}; filename="{book_copy.copy_code}-qr.svg"'
        )
        return response

from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import DigitalBookCategoryForm, DigitalBookForm
from .models import DigitalBook, DigitalBookCategory


class DigitalBookListView(RolePermissionRequiredMixin, ListView):
    model = DigitalBook
    template_name = "digital_library/digitalbook_list.html"
    context_object_name = "digital_books"
    permission_codename = "digital.view_digital_book"

    def get_queryset(self):
        queryset = DigitalBook.objects.select_related("book", "category").prefetch_related("allowed_roles").filter(is_active=True)
        if not self.request.user.is_superuser and not self.request.user.has_role_permission("digital.manage_digital_book"):
            visibility_filter = Q(is_public=True)
            if self.request.user.role_id:
                visibility_filter |= Q(allowed_roles=self.request.user.role)
            queryset = queryset.filter(visibility_filter)
        query = self.request.GET.get("q")
        category = self.request.GET.get("category")
        if query:
            queryset = queryset.filter(title__icontains=query)
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset.distinct().order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = DigitalBookCategory.objects.filter(is_active=True)
        return context


class DigitalBookDetailView(RolePermissionRequiredMixin, DetailView):
    model = DigitalBook
    template_name = "digital_library/digitalbook_detail.html"
    context_object_name = "digital_book"
    permission_codename = "digital.view_digital_book"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.can_access(self.request.user):
            raise Http404("Digital book not found.")
        return obj


class DigitalBookCreateView(RolePermissionRequiredMixin, CreateView):
    model = DigitalBook
    form_class = DigitalBookForm
    template_name = "digital_library/digitalbook_form.html"
    success_url = reverse_lazy("digital_library:list")
    permission_codename = "digital.manage_digital_book"

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, "Digital book uploaded successfully.")
        return super().form_valid(form)


class DigitalBookUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = DigitalBook
    form_class = DigitalBookForm
    template_name = "digital_library/digitalbook_form.html"
    success_url = reverse_lazy("digital_library:list")
    permission_codename = "digital.manage_digital_book"


class DigitalBookDownloadView(RolePermissionRequiredMixin, DetailView):
    model = DigitalBook
    permission_codename = "digital.view_digital_book"

    def get(self, request, *args, **kwargs):
        digital_book = self.get_object()
        if not digital_book.can_access(request.user):
            raise Http404("Digital book not found.")
        digital_book.download_count += 1
        digital_book.save(update_fields=["download_count"])
        return FileResponse(digital_book.file.open("rb"), as_attachment=True, filename=digital_book.file.name.split("/")[-1])


class DigitalCategoryListView(RolePermissionRequiredMixin, ListView):
    model = DigitalBookCategory
    template_name = "digital_library/category_list.html"
    context_object_name = "categories"
    permission_codename = "digital.manage_digital_book"


class DigitalCategoryCreateView(RolePermissionRequiredMixin, CreateView):
    model = DigitalBookCategory
    form_class = DigitalBookCategoryForm
    template_name = "digital_library/category_form.html"
    success_url = reverse_lazy("digital_library:category_list")
    permission_codename = "digital.manage_digital_book"


class DigitalCategoryUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = DigitalBookCategory
    form_class = DigitalBookCategoryForm
    template_name = "digital_library/category_form.html"
    success_url = reverse_lazy("digital_library:category_list")
    permission_codename = "digital.manage_digital_book"

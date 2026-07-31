from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin
from apps.catalog.models import BookCopy

from .forms import (
    DamagedBookForm,
    DamagedBookUpdateForm,
    LostBookForm,
    LostBookUpdateForm,
    RepairRecordForm,
    RepairRecordUpdateForm,
)
from .models import BookStatusLog, DamagedBook, LostBook, RepairRecord
from .services import (
    create_repair_record,
    report_damaged_book,
    report_lost_book,
    update_damaged_record,
    update_lost_record,
    update_repair_status,
)


def add_form_validation_error(form, exc):
    if hasattr(exc, "message_dict"):
        for field, errors in exc.message_dict.items():
            for error in errors:
                form.add_error(field if field in form.fields else None, error)
        return
    for error in exc.messages if hasattr(exc, "messages") else [str(exc)]:
        form.add_error(None, error)


class BookStatusLogListView(RolePermissionRequiredMixin, ListView):
    model = BookStatusLog
    template_name = "status_tracking/status_log_list.html"
    context_object_name = "logs"
    paginate_by = 20
    permission_codename = "status_tracking.view_status"

    def get_queryset(self):
        queryset = BookStatusLog.objects.select_related("book", "book_copy", "changed_by")
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if query:
            queryset = queryset.filter(
                Q(book__title__icontains=query)
                | Q(book__book_code__icontains=query)
                | Q(book_copy__copy_code__icontains=query)
                | Q(reason__icontains=query)
            )
        if status:
            queryset = queryset.filter(new_status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = BookCopy.STATUS_CHOICES
        return context


class LostBookListView(RolePermissionRequiredMixin, ListView):
    model = LostBook
    template_name = "status_tracking/lostbook_list.html"
    context_object_name = "lost_books"
    paginate_by = 20
    permission_codename = "status_tracking.manage_lost"

    def get_queryset(self):
        queryset = LostBook.objects.select_related("book_copy__book", "member__user", "reported_by")
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if query:
            queryset = queryset.filter(
                Q(book_copy__copy_code__icontains=query)
                | Q(book_copy__book__title__icontains=query)
                | Q(member__member_code__icontains=query)
                | Q(member__user__username__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = LostBook.STATUS_CHOICES
        return context


class LostBookDetailView(RolePermissionRequiredMixin, DetailView):
    model = LostBook
    template_name = "status_tracking/lostbook_detail.html"
    context_object_name = "lost_book"
    permission_codename = "status_tracking.manage_lost"


class LostBookCreateView(RolePermissionRequiredMixin, FormView):
    template_name = "status_tracking/lostbook_form.html"
    form_class = LostBookForm
    permission_codename = "status_tracking.manage_lost"

    def form_valid(self, form):
        try:
            record = report_lost_book(
                book_copy=form.cleaned_data["book_copy"],
                borrow_record=form.cleaned_data["borrow_record"],
                member=form.cleaned_data["member"],
                reported_by=self.request.user,
                replacement_cost=form.cleaned_data["replacement_cost"],
                description=form.cleaned_data["description"],
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Lost book record created and book status updated.")
        return redirect("status_tracking:lost_detail", pk=record.pk)


class LostBookUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = LostBook
    form_class = LostBookUpdateForm
    template_name = "status_tracking/lostbook_form.html"
    success_url = reverse_lazy("status_tracking:lost_list")
    permission_codename = "status_tracking.manage_lost"

    def form_valid(self, form):
        try:
            self.object = update_lost_record(
                self.object,
                status=form.cleaned_data["status"],
                replacement_cost=form.cleaned_data["replacement_cost"],
                description=form.cleaned_data["description"],
                resolution_notes=form.cleaned_data["resolution_notes"],
                resolved_date=form.cleaned_data["resolved_date"],
                changed_by=self.request.user,
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Lost book record updated.")
        return redirect(self.success_url)


class DamagedBookListView(RolePermissionRequiredMixin, ListView):
    model = DamagedBook
    template_name = "status_tracking/damagedbook_list.html"
    context_object_name = "damaged_books"
    paginate_by = 20
    permission_codename = "status_tracking.manage_damaged"

    def get_queryset(self):
        queryset = DamagedBook.objects.select_related("book_copy__book", "member__user", "reported_by")
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if query:
            queryset = queryset.filter(
                Q(book_copy__copy_code__icontains=query)
                | Q(book_copy__book__title__icontains=query)
                | Q(member__member_code__icontains=query)
                | Q(member__user__username__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = DamagedBook.STATUS_CHOICES
        return context


class DamagedBookDetailView(RolePermissionRequiredMixin, DetailView):
    model = DamagedBook
    template_name = "status_tracking/damagedbook_detail.html"
    context_object_name = "damaged_book"
    permission_codename = "status_tracking.manage_damaged"


class DamagedBookCreateView(RolePermissionRequiredMixin, FormView):
    template_name = "status_tracking/damagedbook_form.html"
    form_class = DamagedBookForm
    permission_codename = "status_tracking.manage_damaged"

    def form_valid(self, form):
        try:
            record = report_damaged_book(
                book_copy=form.cleaned_data["book_copy"],
                borrow_record=form.cleaned_data["borrow_record"],
                member=form.cleaned_data["member"],
                reported_by=self.request.user,
                severity=form.cleaned_data["severity"],
                estimated_repair_cost=form.cleaned_data["estimated_repair_cost"],
                description=form.cleaned_data["description"],
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Damaged book record created and book status updated.")
        return redirect("status_tracking:damaged_detail", pk=record.pk)


class DamagedBookUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = DamagedBook
    form_class = DamagedBookUpdateForm
    template_name = "status_tracking/damagedbook_form.html"
    success_url = reverse_lazy("status_tracking:damaged_list")
    permission_codename = "status_tracking.manage_damaged"

    def form_valid(self, form):
        try:
            self.object = update_damaged_record(
                self.object,
                status=form.cleaned_data["status"],
                severity=form.cleaned_data["severity"],
                estimated_repair_cost=form.cleaned_data["estimated_repair_cost"],
                description=form.cleaned_data["description"],
                resolution_notes=form.cleaned_data["resolution_notes"],
                resolved_date=form.cleaned_data["resolved_date"],
                changed_by=self.request.user,
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Damaged book record updated.")
        return redirect(self.success_url)


class RepairRecordListView(RolePermissionRequiredMixin, ListView):
    model = RepairRecord
    template_name = "status_tracking/repair_list.html"
    context_object_name = "repairs"
    paginate_by = 20
    permission_codename = "status_tracking.manage_repair"

    def get_queryset(self):
        queryset = RepairRecord.objects.select_related("book_copy__book", "damage_record", "sent_by")
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if query:
            queryset = queryset.filter(
                Q(book_copy__copy_code__icontains=query)
                | Q(book_copy__book__title__icontains=query)
                | Q(vendor__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = RepairRecord.STATUS_CHOICES
        return context


class RepairRecordDetailView(RolePermissionRequiredMixin, DetailView):
    model = RepairRecord
    template_name = "status_tracking/repair_detail.html"
    context_object_name = "repair"
    permission_codename = "status_tracking.manage_repair"


class RepairRecordCreateView(RolePermissionRequiredMixin, FormView):
    template_name = "status_tracking/repair_form.html"
    form_class = RepairRecordForm
    permission_codename = "status_tracking.manage_repair"

    def form_valid(self, form):
        try:
            repair = create_repair_record(
                book_copy=form.cleaned_data["book_copy"],
                sent_by=self.request.user,
                damage_record=form.cleaned_data["damage_record"],
                vendor=form.cleaned_data["vendor"],
                expected_return_date=form.cleaned_data["expected_return_date"],
                repair_cost=form.cleaned_data["repair_cost"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Repair record created and book status updated.")
        return redirect("status_tracking:repair_detail", pk=repair.pk)


class RepairRecordUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = RepairRecord
    form_class = RepairRecordUpdateForm
    template_name = "status_tracking/repair_form.html"
    success_url = reverse_lazy("status_tracking:repair_list")
    permission_codename = "status_tracking.manage_repair"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            update_repair_status(
                self.object,
                status=form.cleaned_data["status"],
                changed_by=self.request.user,
                completed_date=form.cleaned_data["completed_date"],
                notes=form.cleaned_data["notes"],
                vendor=form.cleaned_data["vendor"],
                expected_return_date=form.cleaned_data["expected_return_date"],
                repair_cost=form.cleaned_data["repair_cost"],
            )
        except ValidationError as exc:
            add_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Repair record updated.")
        return redirect(self.success_url)

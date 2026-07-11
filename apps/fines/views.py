from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from apps.accounts.mixins import RolePermissionRequiredMixin
from apps.circulation.models import BorrowRecord

from .forms import (
    FineCreateForm,
    FineUpdateForm,
    FineWaiverForm,
    PaymentForm,
    PaymentVoidForm,
)
from .models import Fine, Payment
from .services import create_fine, record_payment, update_fine, void_payment, waive_fine


class FineListView(RolePermissionRequiredMixin, ListView):
    model = Fine
    template_name = "fines/fine_list.html"
    context_object_name = "fines"
    paginate_by = 20
    permission_codename = "fines.view_fine"

    def get_queryset(self):
        queryset = Fine.objects.select_related(
            "member__user", "borrow_record__book_copy__book", "created_by"
        ).annotate(payment_count=Count("payments")).visible_to(self.request.user)
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        reason = self.request.GET.get("reason", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(member__member_code__icontains=term)
                | Q(member__user__username__icontains=term)
                | Q(member__user__first_name__icontains=term)
                | Q(member__user__last_name__icontains=term)
                | Q(borrow_record__book_copy__book__title__icontains=term)
                | Q(borrow_record__book_copy__copy_code__icontains=term)
                | Q(description__icontains=term)
            )
        if status in dict(Fine.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        if reason in dict(Fine.REASON_CHOICES):
            queryset = queryset.filter(reason=reason)
        return queryset.order_by("status", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = Fine.objects.visible_to(self.request.user)
        outstanding_expression = ExpressionWrapper(
            F("amount") - F("paid_amount"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        totals = visible.aggregate(
            total=Count("id"),
            outstanding_count=Count(
                "id", filter=Q(status__in=[Fine.UNPAID, Fine.PARTIAL])
            ),
            paid_count=Count("id", filter=Q(status=Fine.PAID)),
            waived_count=Count("id", filter=Q(status=Fine.WAIVED)),
            outstanding_balance=Sum(
                outstanding_expression,
                filter=Q(status__in=[Fine.UNPAID, Fine.PARTIAL]),
                default=Decimal("0.00"),
            ),
        )
        context.update(
            {
                "statuses": Fine.STATUS_CHOICES,
                "reasons": Fine.REASON_CHOICES,
                "summary": totals,
            }
        )
        return context


class FineDetailView(RolePermissionRequiredMixin, DetailView):
    model = Fine
    template_name = "fines/fine_detail.html"
    context_object_name = "fine"
    permission_codename = "fines.view_fine"

    def get_queryset(self):
        return (
            Fine.objects.select_related(
                "member__user",
                "borrow_record__book_copy__book",
                "created_by",
                "updated_by",
                "waived_by",
            )
            .prefetch_related("payments__received_by", "payments__voided_by")
            .visible_to(self.request.user)
        )


class FineCreateView(RolePermissionRequiredMixin, FormView):
    form_class = FineCreateForm
    template_name = "fines/fine_form.html"
    permission_codename = "fines.manage_fine"

    def dispatch(self, request, *args, **kwargs):
        self.borrow_record = None
        borrow_id = request.GET.get("borrow") or request.POST.get("borrow_context")
        if borrow_id and str(borrow_id).isdigit():
            self.borrow_record = get_object_or_404(
                BorrowRecord.objects.select_related("member__user", "book_copy__book"),
                pk=borrow_id,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["borrow_record"] = self.borrow_record
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_borrow"] = self.borrow_record
        return context

    def form_valid(self, form):
        try:
            fine = create_fine(
                member=form.cleaned_data["member"],
                borrow_record=form.cleaned_data.get("borrow_record"),
                amount=form.cleaned_data["amount"],
                reason=form.cleaned_data["reason"],
                description=form.cleaned_data["description"],
                created_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Fine created successfully.")
        return redirect("fines:fine_detail", pk=fine.pk)


class FineUpdateView(RolePermissionRequiredMixin, FormView):
    form_class = FineUpdateForm
    template_name = "fines/fine_form.html"
    permission_codename = "fines.manage_fine"

    def dispatch(self, request, *args, **kwargs):
        self.fine = get_object_or_404(Fine.objects.select_related("member__user"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fine"] = self.fine
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fine"] = self.fine
        context["object"] = self.fine
        return context

    def form_valid(self, form):
        try:
            fine = update_fine(
                fine=self.fine,
                amount=form.cleaned_data["amount"],
                reason=form.cleaned_data["reason"],
                description=form.cleaned_data["description"],
                updated_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Fine updated successfully.")
        return redirect("fines:fine_detail", pk=fine.pk)


class FineWaiveView(RolePermissionRequiredMixin, FormView):
    form_class = FineWaiverForm
    template_name = "fines/fine_waive_form.html"
    permission_codename = "fines.manage_fine"

    def dispatch(self, request, *args, **kwargs):
        self.fine = get_object_or_404(Fine.objects.outstanding(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fine"] = self.fine
        return context

    def form_valid(self, form):
        try:
            fine = waive_fine(
                fine=self.fine,
                waived_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Fine waived successfully.")
        return redirect("fines:fine_detail", pk=fine.pk)


class PaymentListView(RolePermissionRequiredMixin, ListView):
    model = Payment
    template_name = "fines/payment_list.html"
    context_object_name = "payments"
    paginate_by = 20
    permission_codename = "fines.view_payment"

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "fine", "member__user", "received_by", "voided_by"
        ).visible_to(self.request.user)
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(member__member_code__icontains=term)
                | Q(member__user__username__icontains=term)
                | Q(member__user__first_name__icontains=term)
                | Q(member__user__last_name__icontains=term)
                | Q(reference_number__icontains=term)
            )
        if status in dict(Payment.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = Payment.objects.visible_to(self.request.user)
        context["statuses"] = Payment.STATUS_CHOICES
        context["summary"] = visible.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=Payment.COMPLETED)),
            voided=Count("id", filter=Q(status=Payment.VOIDED)),
            collected=Sum(
                "amount_paid",
                filter=Q(status=Payment.COMPLETED),
                default=Decimal("0.00"),
            ),
        )
        return context


class PaymentDetailView(RolePermissionRequiredMixin, DetailView):
    model = Payment
    template_name = "fines/payment_detail.html"
    context_object_name = "payment"
    permission_codename = "fines.view_payment"

    def get_queryset(self):
        return Payment.objects.select_related(
            "fine__member__user", "received_by", "voided_by"
        ).visible_to(self.request.user)


class PaymentCreateView(RolePermissionRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = "fines/payment_form.html"
    permission_codename = "fines.receive_payment"

    def dispatch(self, request, *args, **kwargs):
        self.fine = None
        fine_id = kwargs.get("fine_pk") or request.POST.get("fine_context")
        if fine_id:
            self.fine = get_object_or_404(
                Fine.objects.outstanding().select_related("member__user"),
                pk=fine_id,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fine"] = self.fine
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_fine"] = self.fine
        return context

    def form_valid(self, form):
        try:
            payment = record_payment(
                fine=form.cleaned_data["fine"],
                amount_paid=form.cleaned_data["amount_paid"],
                payment_method=form.cleaned_data["payment_method"],
                payment_date=form.cleaned_data["payment_date"],
                reference_number=form.cleaned_data["reference_number"],
                notes=form.cleaned_data["notes"],
                received_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Fine payment recorded successfully.")
        return redirect("fines:payment_detail", pk=payment.pk)


class PaymentVoidView(RolePermissionRequiredMixin, FormView):
    form_class = PaymentVoidForm
    template_name = "fines/payment_void_form.html"
    permission_codename = "fines.receive_payment"

    def dispatch(self, request, *args, **kwargs):
        self.payment = get_object_or_404(
            Payment.objects.select_related("fine", "member__user"),
            pk=kwargs["pk"],
            status=Payment.COMPLETED,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment"] = self.payment
        return context

    def form_valid(self, form):
        try:
            payment = void_payment(
                payment=self.payment,
                voided_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Payment voided and fine balance recalculated.")
        return redirect("fines:payment_detail", pk=payment.pk)

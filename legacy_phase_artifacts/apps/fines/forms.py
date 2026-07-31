from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.circulation.models import BorrowRecord
from apps.members.models import Member

from .models import Fine, Payment


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, member):
        return f"{member.member_code} - {member.display_name}"


class BorrowChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, record):
        return (
            f"{record.member.member_code} - {record.book_copy.book.title} "
            f"({record.book_copy.copy_code})"
        )


class FineChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, fine):
        return (
            f"#{fine.pk} - {fine.member.member_code} - "
            f"{fine.get_reason_display()} - balance {fine.balance}"
        )


class FineCreateForm(BootstrapFormMixin, forms.Form):
    borrow_record = BorrowChoiceField(
        queryset=BorrowRecord.objects.none(),
        required=False,
        help_text="Required for late-return fines.",
    )
    member = MemberChoiceField(queryset=Member.objects.none())
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    reason = forms.ChoiceField(choices=Fine.REASON_CHOICES)
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, borrow_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["reason"].initial = Fine.OTHER
        self.fields["member"].queryset = Member.objects.select_related("user").order_by(
            "member_code"
        )
        borrows = BorrowRecord.objects.select_related(
            "member__user", "book_copy__book"
        ).order_by("-borrow_date", "-created_at")
        if borrow_record:
            borrows = borrows.filter(pk=borrow_record.pk)
            self.fields["borrow_record"].initial = borrow_record
            self.fields["borrow_record"].disabled = True
            self.fields["member"].initial = borrow_record.member
            self.fields["member"].disabled = True
        self.fields["borrow_record"].queryset = borrows
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        borrow_record = cleaned.get("borrow_record")
        member = cleaned.get("member")
        reason = cleaned.get("reason")
        if borrow_record and member and borrow_record.member_id != member.pk:
            self.add_error("member", "Fine member must match the borrow record member.")
        if reason == Fine.LATE_RETURN and not borrow_record:
            self.add_error("borrow_record", "Late-return fines require a borrow record.")
        return cleaned


class FineUpdateForm(BootstrapFormMixin, forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    reason = forms.ChoiceField(choices=Fine.REASON_CHOICES)
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, fine=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fine and not self.is_bound:
            self.initial.update(
                {
                    "amount": fine.amount,
                    "reason": fine.reason,
                    "description": fine.description,
                }
            )
        self.apply_bootstrap()


class FineWaiverForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(
        label="Waiver reason",
        widget=forms.Textarea(attrs={"rows": 4}),
        min_length=5,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class PaymentForm(BootstrapFormMixin, forms.Form):
    fine = FineChoiceField(queryset=Fine.objects.none())
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    payment_method = forms.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    payment_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    reference_number = forms.CharField(max_length=120, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, fine=None, **kwargs):
        super().__init__(*args, **kwargs)
        fines = Fine.objects.outstanding().select_related("member__user")
        if fine:
            fines = fines.filter(pk=fine.pk)
            self.fields["fine"].initial = fine
            self.fields["fine"].disabled = True
            if not self.is_bound:
                self.fields["amount_paid"].initial = fine.balance
        self.fields["fine"].queryset = fines.order_by("member__member_code", "created_at")
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        fine = cleaned.get("fine")
        amount = cleaned.get("amount_paid")
        payment_date = cleaned.get("payment_date")
        if fine and not fine.is_outstanding:
            self.add_error("fine", "Payments can only be recorded against outstanding fines.")
        if fine and amount and amount > fine.balance:
            self.add_error(
                "amount_paid",
                f"Payment cannot exceed remaining balance: {fine.balance}.",
            )
        if payment_date and payment_date > timezone.localdate():
            self.add_error("payment_date", "Payment date cannot be in the future.")
        return cleaned


class PaymentVoidForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(
        label="Void reason",
        widget=forms.Textarea(attrs={"rows": 4}),
        min_length=5,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

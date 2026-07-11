from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import BookCopy

from .models import DamagedBook, LostBook, RepairRecord


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class BookCopyChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.copy_code} - {obj.book.title} ({obj.get_status_display()})"


class BorrowRecordChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.member.display_name} - {obj.book_copy.copy_code} ({obj.get_status_display()})"


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.member_code} - {obj.display_name}"


class DamagedBookChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.book_copy.copy_code} - {obj.get_status_display()} damage"


def _book_copy_queryset():
    return BookCopy.objects.select_related("book").order_by("book__title", "copy_code")


def _validate_common_report_fields(cleaned_data):
    book_copy = cleaned_data.get("book_copy")
    borrow_record = cleaned_data.get("borrow_record")
    member = cleaned_data.get("member")
    if borrow_record and book_copy and borrow_record.book_copy_id != book_copy.pk:
        raise ValidationError("Borrow record must belong to the selected book copy.")
    if borrow_record and member and borrow_record.member_id != member.pk:
        raise ValidationError("Member must match the selected borrow record.")
    if not member and borrow_record:
        cleaned_data["member"] = borrow_record.member
    return cleaned_data


class LostBookForm(BootstrapFormMixin, forms.Form):
    book_copy = BookCopyChoiceField(queryset=_book_copy_queryset())
    borrow_record = BorrowRecordChoiceField(queryset=None, required=False)
    member = MemberChoiceField(queryset=None, required=False)
    replacement_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=0,
    )
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.circulation.models import BorrowRecord
        from apps.members.models import Member

        self.fields["book_copy"].queryset = _book_copy_queryset()
        self.fields["borrow_record"].queryset = BorrowRecord.objects.select_related(
            "member__user", "book_copy__book"
        ).order_by("-borrow_date", "-created_at")
        self.fields["member"].queryset = Member.objects.select_related("user").order_by("member_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        return _validate_common_report_fields(cleaned_data)


class LostBookUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LostBook
        fields = ["status", "replacement_cost", "description", "resolution_notes", "resolved_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "resolution_notes": forms.Textarea(attrs={"rows": 3}),
            "resolved_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["replacement_cost"].min_value = Decimal("0.00")
        self.apply_bootstrap()

    def clean_resolved_date(self):
        value = self.cleaned_data.get("resolved_date")
        if value and value > timezone.localdate():
            raise ValidationError("Resolved date cannot be in the future.")
        return value


class DamagedBookForm(BootstrapFormMixin, forms.Form):
    book_copy = BookCopyChoiceField(queryset=_book_copy_queryset())
    borrow_record = BorrowRecordChoiceField(queryset=None, required=False)
    member = MemberChoiceField(queryset=None, required=False)
    severity = forms.ChoiceField(choices=DamagedBook.SEVERITY_CHOICES)
    estimated_repair_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=0,
    )
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.circulation.models import BorrowRecord
        from apps.members.models import Member

        self.fields["book_copy"].queryset = _book_copy_queryset()
        self.fields["borrow_record"].queryset = BorrowRecord.objects.select_related(
            "member__user", "book_copy__book"
        ).order_by("-borrow_date", "-created_at")
        self.fields["member"].queryset = Member.objects.select_related("user").order_by("member_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        return _validate_common_report_fields(cleaned_data)


class DamagedBookUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DamagedBook
        fields = [
            "status",
            "severity",
            "estimated_repair_cost",
            "description",
            "resolution_notes",
            "resolved_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "resolution_notes": forms.Textarea(attrs={"rows": 3}),
            "resolved_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estimated_repair_cost"].min_value = Decimal("0.00")
        self.apply_bootstrap()

    def clean_resolved_date(self):
        value = self.cleaned_data.get("resolved_date")
        if value and value > timezone.localdate():
            raise ValidationError("Resolved date cannot be in the future.")
        return value


class RepairRecordForm(BootstrapFormMixin, forms.Form):
    book_copy = BookCopyChoiceField(queryset=_book_copy_queryset())
    damage_record = DamagedBookChoiceField(queryset=DamagedBook.objects.none(), required=False)
    vendor = forms.CharField(max_length=160, required=False)
    expected_return_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    repair_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=0,
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["book_copy"].queryset = _book_copy_queryset()
        self.fields["damage_record"].queryset = DamagedBook.objects.select_related(
            "book_copy__book"
        ).open().order_by("book_copy__book__title", "book_copy__copy_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        book_copy = cleaned_data.get("book_copy")
        damage_record = cleaned_data.get("damage_record")
        expected_return_date = cleaned_data.get("expected_return_date")
        if damage_record and book_copy and damage_record.book_copy_id != book_copy.pk:
            raise ValidationError("Damage record must belong to the selected book copy.")
        if expected_return_date and expected_return_date < timezone.localdate():
            raise ValidationError("Expected return date cannot be in the past.")
        return cleaned_data


class RepairRecordUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RepairRecord
        fields = ["status", "vendor", "expected_return_date", "completed_date", "repair_cost", "notes"]
        widgets = {
            "expected_return_date": forms.DateInput(attrs={"type": "date"}),
            "completed_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["repair_cost"].min_value = Decimal("0.00")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        sent_date = self.instance.sent_date
        expected_return_date = cleaned_data.get("expected_return_date")
        completed_date = cleaned_data.get("completed_date")
        if expected_return_date and sent_date and expected_return_date < sent_date:
            raise ValidationError("Expected return date cannot be earlier than sent date.")
        if completed_date and sent_date and completed_date < sent_date:
            raise ValidationError("Completed date cannot be earlier than sent date.")
        if completed_date and completed_date > timezone.localdate():
            raise ValidationError("Completed date cannot be in the future.")
        return cleaned_data

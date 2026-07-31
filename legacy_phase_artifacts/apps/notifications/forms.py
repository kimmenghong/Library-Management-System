from django import forms

from apps.catalog.models import BookCopy
from apps.circulation.models import BorrowRecord
from apps.members.models import Member

from .models import Notification


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
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


class CopyChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, copy):
        return f"{copy.copy_code} - {copy.book.title}"


class ManualNotificationForm(BootstrapFormMixin, forms.ModelForm):
    recipient = MemberChoiceField(queryset=Member.objects.none())
    related_borrow_record = BorrowChoiceField(
        queryset=BorrowRecord.objects.none(),
        required=False,
    )
    related_book_copy = CopyChoiceField(
        queryset=BookCopy.objects.none(),
        required=False,
    )

    class Meta:
        model = Notification
        fields = [
            "recipient",
            "title",
            "message",
            "notification_type",
            "channel",
            "priority",
            "related_borrow_record",
            "related_book_copy",
        ]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = Member.objects.select_related("user").order_by(
            "member_code"
        )
        self.fields["related_borrow_record"].queryset = BorrowRecord.objects.select_related(
            "member__user", "book_copy__book"
        ).order_by("-borrow_date", "-created_at")
        self.fields["related_book_copy"].queryset = BookCopy.objects.select_related(
            "book"
        ).order_by("book__title", "copy_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        recipient = cleaned.get("recipient")
        borrow = cleaned.get("related_borrow_record")
        copy = cleaned.get("related_book_copy")
        if recipient and borrow and borrow.member_id != recipient.pk:
            self.add_error("recipient", "Recipient must match the borrow record member.")
        if borrow and copy and borrow.book_copy_id != copy.pk:
            self.add_error("related_book_copy", "Book copy must match the borrow record.")
        return cleaned


class ReminderRunForm(BootstrapFormMixin, forms.Form):
    due_within_days = forms.IntegerField(min_value=0, max_value=30, initial=3)
    send_due_date_reminders = forms.BooleanField(required=False, initial=True)
    send_overdue_reminders = forms.BooleanField(required=False, initial=True)
    send_email = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("send_due_date_reminders") and not cleaned.get(
            "send_overdue_reminders"
        ):
            raise forms.ValidationError("Select at least one reminder type.")
        return cleaned

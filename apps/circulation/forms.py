from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone

from apps.catalog.models import Book, BookCopy
from apps.members.models import Member

from .models import BorrowRecord, BorrowingPolicy, Reservation, ReturnRecord


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, member):
        return f"{member.member_code} - {member.display_name}"


class CopyChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, copy):
        return f"{copy.copy_code} - {copy.book.title}"


class BorrowChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, record):
        return (
            f"{record.member.member_code} - {record.book_copy.copy_code} - "
            f"due {record.due_date:%Y-%m-%d}"
        )


class BorrowingPolicyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BorrowingPolicy
        fields = [
            "member_type",
            "max_books",
            "loan_period_days",
            "renewal_days",
            "max_renewals",
            "fine_per_day",
            "reservation_expiry_days",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["member_type"].disabled = True
        self.apply_bootstrap()


class BorrowBookForm(BootstrapFormMixin, forms.Form):
    member = MemberChoiceField(queryset=Member.objects.none())
    book_copy = CopyChoiceField(queryset=BookCopy.objects.none())
    borrow_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=timezone.localdate,
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
        help_text="Leave blank to apply the member's borrowing policy.",
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = Member.objects.active().select_related(
            "user", "user__role"
        ).order_by("member_code")
        self.fields["book_copy"].queryset = BookCopy.objects.select_related(
            "book"
        ).filter(status=BookCopy.AVAILABLE).order_by("book__title", "copy_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        borrow_date = cleaned_data.get("borrow_date")
        due_date = cleaned_data.get("due_date")
        if borrow_date and borrow_date > timezone.localdate():
            self.add_error("borrow_date", "Borrow date cannot be in the future.")
        if borrow_date and due_date and due_date < borrow_date:
            self.add_error("due_date", "Due date cannot be earlier than borrow date.")
        return cleaned_data


class ReturnBookForm(BootstrapFormMixin, forms.Form):
    borrow_record = BorrowChoiceField(queryset=BorrowRecord.objects.none())
    return_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=timezone.localdate,
    )
    book_condition = forms.ChoiceField(choices=ReturnRecord.CONDITION_CHOICES)
    remarks = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, borrow_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = BorrowRecord.objects.active().select_related(
            "member__user", "book_copy__book"
        )
        if borrow_record:
            queryset = queryset.filter(pk=borrow_record.pk)
            self.fields["borrow_record"].initial = borrow_record
            self.fields["borrow_record"].disabled = True
        self.fields["borrow_record"].queryset = queryset.order_by("due_date")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        record = cleaned_data.get("borrow_record")
        return_date = cleaned_data.get("return_date")
        if record and not record.is_active:
            self.add_error("borrow_record", "This borrow record is not active.")
        if return_date and return_date > timezone.localdate():
            self.add_error("return_date", "Return date cannot be in the future.")
        if record and return_date and return_date < record.borrow_date:
            self.add_error("return_date", "Return date cannot be earlier than borrow date.")
        return cleaned_data


class RenewalForm(BootstrapFormMixin, forms.Form):
    remarks = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ReservationForm(BootstrapFormMixin, forms.Form):
    member = MemberChoiceField(queryset=Member.objects.none())
    book = forms.ModelChoiceField(queryset=Book.objects.none())
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, actor=None, book=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        members = Member.objects.active().select_related("user", "user__role")
        if actor and not (
            actor.is_superuser
            or actor.has_role("super_admin", "admin", "librarian", "assistant_librarian")
        ):
            member = getattr(actor, "member_profile", None)
            members = members.filter(pk=getattr(member, "pk", None))
            if member:
                self.fields["member"].initial = member
                self.fields["member"].disabled = True
        self.fields["member"].queryset = members.order_by("member_code")

        books = (
            Book.objects.annotate(
                copy_count=Count("copies", distinct=True),
                available_count=Count(
                    "copies",
                    filter=Q(copies__status=BookCopy.AVAILABLE),
                    distinct=True,
                )
            )
            .filter(copy_count__gt=0, available_count=0)
            .order_by("title")
        )
        if book:
            books = books.filter(pk=book.pk)
            self.fields["book"].initial = book
            self.fields["book"].disabled = True
        self.fields["book"].queryset = books
        self.apply_bootstrap()

    def clean_member(self):
        member = self.cleaned_data["member"]
        if self.actor and not (
            self.actor.is_superuser
            or self.actor.has_role(
                "super_admin", "admin", "librarian", "assistant_librarian"
            )
        ) and member.user_id != self.actor.pk:
            raise ValidationError("You can only create reservations for your own account.")
        return member


class ReservationStatusForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(choices=[])
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, actor=None, reservation=None, **kwargs):
        self.actor = actor
        self.reservation = reservation
        super().__init__(*args, **kwargs)
        is_operator = bool(
            actor
            and (
                actor.is_superuser
                or actor.has_role(
                    "super_admin", "admin", "librarian", "assistant_librarian"
                )
            )
        )
        if is_operator:
            if reservation and reservation.status == Reservation.PENDING:
                choices = [
                    (Reservation.READY, "Ready for Pickup"),
                    (Reservation.CANCELLED, "Cancelled"),
                ]
            else:
                choices = [
                    (Reservation.CANCELLED, "Cancelled"),
                    (Reservation.EXPIRED, "Expired"),
                ]
        else:
            choices = [(Reservation.CANCELLED, "Cancel Reservation")]
        self.fields["status"].choices = choices
        self.apply_bootstrap()

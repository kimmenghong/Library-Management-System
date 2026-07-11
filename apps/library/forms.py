from decimal import Decimal
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    UserCreationForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Author,
    Book,
    BorrowRecord,
    Category,
    Fine,
    Member,
    Notification,
    Publisher,
    Report,
    Role,
    User,
)


class BootstrapFormMixin:
    """Apply Bootstrap classes consistently without repeating widget declarations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"
            else:
                css_class = "form-control"
            widget.attrs["class"] = (
                f"{widget.attrs.get('class', '')} {css_class}".strip()
            )


class RoleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Role
        fields = ["role_name", "description"]


class UserCreateForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "role",
            "username",
            "email",
            "full_name",
            "phone",
            "address",
            "is_active",
            "is_staff",
        ]


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "role",
            "username",
            "email",
            "full_name",
            "phone",
            "address",
            "is_active",
            "is_staff",
        ]


class SupabaseAuthLoginForm(BootstrapFormMixin, forms.Form):
    """Collect credentials for Supabase Auth email/password sign-in."""

    email = forms.CharField(
        label="Email address",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SupabaseAuthRegisterForm(BootstrapFormMixin, forms.Form):
    """Collect Supabase credentials and local profile data for registration."""

    full_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100, widget=forms.EmailInput())
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "A local library account already exists for this email. "
                "Please sign in instead."
            )
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned_data


class UserAdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "role",
            "username",
            "email",
            "full_name",
            "phone",
            "address",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = [
            "role",
            "username",
            "password",
            "email",
            "full_name",
            "phone",
            "address",
            "is_active",
            "is_staff",
            "is_superuser",
        ]

    def clean_password(self):
        return self.initial["password"]


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["category_name", "description"]


class AuthorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Author
        fields = ["author_name", "biography"]


class PublisherForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Publisher
        fields = [
            "publisher_name",
            "address",
            "contact_number",
            "email",
        ]


class BookForm(BootstrapFormMixin, forms.ModelForm):
    """Validate and style book catalog input."""

    class Meta:
        model = Book
        fields = [
            "category",
            "author",
            "publisher",
            "isbn",
            "title",
            "edition",
            "publication_year",
            "quantity",
            "available_quantity",
            "shelf_location",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.order_by("category_name")
        self.fields["author"].queryset = Author.objects.order_by("author_name")
        self.fields["publisher"].queryset = Publisher.objects.order_by("publisher_name")


class MemberForm(BootstrapFormMixin, forms.ModelForm):
    """Create or update a library member without reusing another member's user."""

    class Meta:
        model = Member
        fields = [
            "user",
            "member_code",
            "member_type",
            "department",
            "phone",
            "address",
            "registration_date",
            "status",
        ]
        widgets = {"registration_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used_user_ids = Member.objects.exclude(pk=self.instance.pk).values_list(
            "user_id", flat=True
        )
        self.fields["user"].queryset = (
            User.objects.select_related("role")
            .exclude(user_id__in=used_user_ids)
            .order_by("full_name", "username")
        )


class BorrowForm(BootstrapFormMixin, forms.ModelForm):
    """Issue an available title to an active member."""

    class Meta:
        model = BorrowRecord
        fields = ["member", "book", "borrow_date", "due_date"]
        widgets = {
            "borrow_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = Member.objects.select_related("user").filter(
            status=Member.ACTIVE
        )
        self.fields["book"].queryset = Book.objects.select_related(
            "author", "category", "publisher"
        ).filter(available_quantity__gt=0, status=Book.AVAILABLE)

    def clean_book(self):
        book = self.cleaned_data["book"]
        if book.available_quantity < 1:
            raise ValidationError("This book is not currently available.")
        return book


class ReturnForm(BootstrapFormMixin, forms.Form):
    return_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, borrow_record=None, **kwargs):
        self.borrow_record = borrow_record
        super().__init__(*args, **kwargs)

    def clean_return_date(self):
        return_date = self.cleaned_data["return_date"]
        if self.borrow_record and return_date < self.borrow_record.borrow_date:
            raise ValidationError("Return date cannot be earlier than the borrow date.")
        return return_date


class FineForm(BootstrapFormMixin, forms.ModelForm):
    """Manual fine form kept for administrative corrections."""

    class Meta:
        model = Fine
        fields = [
            "borrow",
            "member",
            "amount",
            "paid_amount",
            "status",
            "paid_date",
        ]
        widgets = {"paid_date": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["borrow"].queryset = BorrowRecord.objects.select_related(
            "member__user", "book"
        )
        self.fields["member"].queryset = Member.objects.select_related("user")


class FinePaymentForm(BootstrapFormMixin, forms.Form):
    payment_amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
    )

    def __init__(self, *args, fine=None, **kwargs):
        self.fine = fine
        super().__init__(*args, **kwargs)
        if fine:
            self.fields["payment_amount"].max_value = fine.balance
            self.fields["payment_amount"].help_text = (
                f"Outstanding balance: {fine.balance}"
            )

    def clean_payment_amount(self):
        amount = self.cleaned_data["payment_amount"]
        if self.fine and amount > self.fine.balance:
            raise ValidationError("Payment cannot exceed the outstanding balance.")
        return amount


class NotificationForm(BootstrapFormMixin, forms.ModelForm):
    """Create member-facing notification history records."""

    class Meta:
        model = Notification
        fields = [
            "member",
            "title",
            "message",
            "notification_type",
            "is_read",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = Member.objects.select_related("user").order_by(
            "member_code"
        )


class ReportForm(BootstrapFormMixin, forms.ModelForm):
    """Generate or attach a CSV report file safely."""

    class Meta:
        model = Report
        fields = ["report_type", "file_path"]

    def clean_file_path(self):
        file = self.cleaned_data.get("file_path")
        if not file:
            return file

        allowed_extensions = {
            item.lower()
            for item in getattr(settings, "REPORT_UPLOAD_ALLOWED_EXTENSIONS", [".csv"])
        }
        extension = Path(file.name).suffix.lower()
        if extension not in allowed_extensions:
            raise ValidationError(
                "Only CSV report files are allowed for manual upload."
            )

        max_size = getattr(settings, "REPORT_UPLOAD_MAX_SIZE", 2 * 1024 * 1024)
        if file.size > max_size:
            raise ValidationError("Report file exceeds the configured size limit.")

        return file

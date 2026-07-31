from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

from .models import Permission, Role, User


PROTECTED_ROLE_SLUGS = (Role.SUPER_ADMIN, Role.ADMIN)


class BootstrapFormMixin:
    """Apply Bootstrap 5 classes consistently without repeating widget markup."""

    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                css_class = "permission-grid"
            elif isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()


class CaseInsensitiveEmailMixin:
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        queryset = User.objects.filter(email__iexact=email)
        if getattr(self.instance, "pk", None):
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("A user with this email address already exists.")
        return email


class AccountAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
        self.fields["username"].widget.attrs.update(
            {"autofocus": True, "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser and user.role and not user.role.is_active:
            raise ValidationError(
                "Your assigned role is inactive. Contact a system administrator.",
                code="inactive_role",
            )


class AccountPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
        self.fields["email"].widget.attrs.update(
            {"autocomplete": "email", "placeholder": "name@example.com"}
        )


class AccountSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
        for field in self.fields.values():
            field.widget.attrs["autocomplete"] = "new-password"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = False
        if commit:
            user.save(update_fields=["password", "must_change_password"])
        return user


class AccountPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
        self.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = False
        if commit:
            user.save(update_fields=["password", "must_change_password"])
        return user


class UserCreateForm(CaseInsensitiveEmailMixin, BootstrapFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
            "is_active",
            "is_staff",
            "must_change_password",
        ]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.filter(is_active=True).order_by("name")
        self.fields["role"].required = True
        if not actor or not actor.is_superuser:
            self.fields["role"].queryset = self.fields["role"].queryset.exclude(
                slug__in=PROTECTED_ROLE_SLUGS
            )
            self.fields.pop("is_staff", None)
        self.apply_bootstrap()

    def clean_role(self):
        role = self.cleaned_data["role"]
        if (
            role
            and role.slug in PROTECTED_ROLE_SLUGS
            and (not self.actor or not self.actor.is_superuser)
        ):
            raise ValidationError("Only a superuser can assign this protected role.")
        return role


class UserUpdateForm(CaseInsensitiveEmailMixin, BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
            "avatar",
            "is_active",
            "is_staff",
            "must_change_password",
        ]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.filter(is_active=True).order_by("name")
        self.fields["role"].required = True
        if not actor or not actor.is_superuser:
            self.fields["role"].queryset = self.fields["role"].queryset.exclude(
                slug__in=PROTECTED_ROLE_SLUGS
            )
            self.fields.pop("is_staff", None)
        self.fields["avatar"].widget.attrs["accept"] = ".jpg,.jpeg,.png,.webp"
        self.apply_bootstrap()

    def clean_role(self):
        role = self.cleaned_data["role"]
        if (
            role
            and role.slug in PROTECTED_ROLE_SLUGS
            and (not self.actor or not self.actor.is_superuser)
        ):
            raise ValidationError("Only a superuser can assign this protected role.")
        return role


class ProfileUpdateForm(CaseInsensitiveEmailMixin, BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "avatar"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].widget.attrs["accept"] = ".jpg,.jpeg,.png,.webp"
        self.apply_bootstrap()


class RoleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name", "slug", "description", "permissions", "is_system", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "permissions": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = Permission.objects.filter(
            is_active=True
        ).order_by("module", "action", "name")
        if not actor or not actor.is_superuser:
            self.fields.pop("is_system", None)
        elif self.instance.pk and self.instance.is_system:
            self.fields["slug"].disabled = True
            self.fields["is_system"].disabled = True
        self.apply_bootstrap()

    def clean_slug(self):
        return self.cleaned_data["slug"].strip().lower()


class PermissionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Permission
        fields = ["name", "codename", "module", "action", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_codename(self):
        codename = self.cleaned_data["codename"].strip().lower()
        if codename.count(".") != 1 or " " in codename:
            raise ValidationError("Use the format 'module.action_name' without spaces.")
        return codename

    def clean(self):
        cleaned_data = super().clean()
        codename = cleaned_data.get("codename")
        module = cleaned_data.get("module")
        if codename and module and not codename.startswith(f"{module}."):
            self.add_error("codename", f"Codename must start with '{module}.'.")
        return cleaned_data

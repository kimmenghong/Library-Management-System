from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role

from .models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile


User = get_user_model()


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


class MemberUserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, user):
        role = user.role.name if user.role else "No role"
        return f"{user.full_name} ({user.username}) - {role}"


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, member):
        return f"{member.member_code} - {member.display_name}"


class MemberForm(BootstrapFormMixin, forms.ModelForm):
    user = MemberUserChoiceField(queryset=User.objects.none())

    class Meta:
        model = Member
        fields = [
            "user",
            "member_type",
            "phone",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "status",
            "joined_date",
            "expiry_date",
            "notes",
        ]
        widgets = {
            "joined_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        eligible_roles = [value for value, _label in Member.MEMBER_TYPE_CHOICES]
        queryset = (
            User.objects.select_related("role")
            .filter(is_active=True, is_superuser=False)
            .filter(Q(role__slug__in=eligible_roles) | Q(role__isnull=True))
            .exclude(member_profile__isnull=False)
            .order_by("first_name", "last_name", "username")
        )

        if self.instance.pk:
            queryset = User.objects.select_related("role").filter(pk=self.instance.user_id)
            self.fields["user"].disabled = True
            self.fields.pop("status", None)
            if self.instance.specialized_profile:
                self.fields["member_type"].disabled = True
        self.fields["user"].queryset = queryset
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        joined_date = cleaned_data.get("joined_date")
        expiry_date = cleaned_data.get("expiry_date")
        if joined_date and expiry_date and expiry_date < joined_date:
            self.add_error(
                "expiry_date",
                "Expiry date cannot be earlier than the joined date.",
            )
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=commit)
        if commit and not member.user.role_id:
            role = Role.objects.filter(slug=member.member_type, is_active=True).first()
            if role:
                member.user.role = role
                member.user.save(update_fields=["role", "updated_at"])
        return member


class MemberStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Member
        fields = ["status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].label = "Administrative notes"
        self.apply_bootstrap()

    def clean_status(self):
        status = self.cleaned_data["status"]
        if status == Member.ACTIVE:
            if not self.instance.user.is_active:
                raise ValidationError("An inactive user account cannot have active membership.")
            if self.instance.user.role and not self.instance.user.role.is_active:
                raise ValidationError("A user with an inactive role cannot have active membership.")
            if self.instance.expiry_date and self.instance.expiry_date < timezone.localdate():
                raise ValidationError("Renew the membership expiry date before activating it.")
        return status


class SpecializedProfileForm(BootstrapFormMixin, forms.ModelForm):
    allowed_member_types = ()
    profile_relation = ""
    identifier_field = ""
    member = MemberChoiceField(queryset=Member.objects.none())

    def __init__(self, *args, member=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Member.objects.select_related("user").filter(
            member_type__in=self.allowed_member_types
        )
        queryset = queryset.filter(
            student_profile__isnull=True,
            teacher_profile__isnull=True,
            staff_profile__isnull=True,
            librarian_profile__isnull=True,
        )

        if self.instance.pk:
            queryset = Member.objects.select_related("user").filter(
                pk=self.instance.member_id
            )
            self.fields["member"].disabled = True
        elif member:
            queryset = queryset.filter(pk=member.pk)
            self.fields["member"].initial = member
            self.fields["member"].disabled = True

        self.fields["member"].queryset = queryset.order_by("member_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get(self.identifier_field)
        if identifier:
            identifier = identifier.strip().upper()
            cleaned_data[self.identifier_field] = identifier
            lookup = {f"{self.identifier_field}__iexact": identifier}
            queryset = self._meta.model.objects.filter(**lookup)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error(
                    self.identifier_field,
                    "A profile with this institutional ID already exists.",
                )
        return cleaned_data


class StudentProfileForm(SpecializedProfileForm):
    allowed_member_types = (Member.STUDENT,)
    profile_relation = "student_profile"
    identifier_field = "student_id"

    class Meta:
        model = StudentProfile
        fields = [
            "member",
            "student_id",
            "department",
            "program",
            "year_level",
            "semester",
            "enrollment_date",
            "guardian_name",
            "guardian_phone",
        ]
        widgets = {"enrollment_date": forms.DateInput(attrs={"type": "date"})}


class TeacherProfileForm(SpecializedProfileForm):
    allowed_member_types = (Member.TEACHER,)
    profile_relation = "teacher_profile"
    identifier_field = "teacher_id"

    class Meta:
        model = TeacherProfile
        fields = [
            "member",
            "teacher_id",
            "faculty",
            "department",
            "designation",
            "office",
            "employment_date",
        ]
        widgets = {"employment_date": forms.DateInput(attrs={"type": "date"})}


class StaffProfileForm(SpecializedProfileForm):
    allowed_member_types = (Member.STAFF,)
    profile_relation = "staff_profile"
    identifier_field = "staff_id"

    class Meta:
        model = StaffProfile
        fields = [
            "member",
            "staff_id",
            "department",
            "position",
            "office",
            "employment_date",
        ]
        widgets = {"employment_date": forms.DateInput(attrs={"type": "date"})}


class LibrarianProfileForm(SpecializedProfileForm):
    allowed_member_types = (Member.LIBRARIAN, Member.ASSISTANT_LIBRARIAN)
    profile_relation = "librarian_profile"
    identifier_field = "librarian_id"

    class Meta:
        model = LibrarianProfile
        fields = [
            "member",
            "librarian_id",
            "employee_type",
            "department",
            "shift",
            "hire_date",
            "can_approve_overrides",
        ]
        widgets = {"hire_date": forms.DateInput(attrs={"type": "date"})}

    def clean_employee_type(self):
        employee_type = self.cleaned_data["employee_type"]
        member = self.cleaned_data.get("member") or getattr(self.instance, "member", None)
        if member and employee_type != member.member_type:
            raise ValidationError("Employee type must match the member type.")
        return employee_type

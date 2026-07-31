import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9 ()-]{6,24}$",
    message="Enter a valid phone number using digits, spaces, parentheses, +, or -.",
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MemberQuerySet(models.QuerySet):
    def active(self):
        today = timezone.localdate()
        return (
            self.filter(status=Member.ACTIVE, user__is_active=True)
            .filter(Q(user__role__isnull=True) | Q(user__role__is_active=True))
            .filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
        )


class Member(TimeStampedModel):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"
    LIBRARIAN = "librarian"
    ASSISTANT_LIBRARIAN = "assistant_librarian"

    MEMBER_TYPE_CHOICES = [
        (STUDENT, "Student"),
        (TEACHER, "Teacher"),
        (STAFF, "Staff"),
        (LIBRARIAN, "Librarian"),
        (ASSISTANT_LIBRARIAN, "Assistant Librarian"),
    ]
    MEMBER_TYPE_VALUES = {value for value, _label in MEMBER_TYPE_CHOICES}
    CODE_PREFIXES = {
        STUDENT: "STU",
        TEACHER: "TCH",
        STAFF: "STF",
        LIBRARIAN: "LIB",
        ASSISTANT_LIBRARIAN: "ALB",
    }

    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (PENDING, "Pending"),
        (SUSPENDED, "Suspended"),
        (EXPIRED, "Expired"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )
    member_code = models.CharField(max_length=30, unique=True, blank=True, editable=False)
    member_type = models.CharField(max_length=30, choices=MEMBER_TYPE_CHOICES)
    phone = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        validators=[phone_validator],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    joined_date = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = MemberQuerySet.as_manager()

    class Meta:
        ordering = ["member_code", "user__username"]
        indexes = [models.Index(fields=["member_type", "status"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(expiry_date__isnull=True) | Q(expiry_date__gte=models.F("joined_date")),
                name="member_expiry_on_or_after_joined",
            )
        ]

    def clean(self):
        errors = {}
        if self.expiry_date and self.joined_date and self.expiry_date < self.joined_date:
            errors["expiry_date"] = "Expiry date cannot be earlier than the joined date."

        if self.user_id:
            role = getattr(self.user, "role", None)
            if role and role.slug in self.MEMBER_TYPE_VALUES and role.slug != self.member_type:
                errors["member_type"] = (
                    f"Member type must match the user's {role.name} role."
                )

        if self.pk:
            previous_type = (
                Member.objects.filter(pk=self.pk)
                .values_list("member_type", flat=True)
                .first()
            )
            if previous_type and previous_type != self.member_type and self.specialized_profile:
                errors["member_type"] = (
                    "Remove the existing specialized profile before changing member type."
                )

        if errors:
            raise ValidationError(errors)

    def _generate_member_code(self):
        prefix = self.CODE_PREFIXES[self.member_type]
        year = timezone.localdate().year
        for _attempt in range(10):
            token = uuid.uuid4().hex[:8].upper()
            candidate = f"{prefix}-{year}-{token}"
            if not Member.objects.filter(member_code=candidate).exists():
                return candidate
        raise RuntimeError("Unable to generate a unique member code.")

    def save(self, *args, **kwargs):
        if not self.member_code:
            self.member_code = self._generate_member_code()

        status_changed = False
        if (
            self.expiry_date
            and self.expiry_date < timezone.localdate()
            and self.status == self.ACTIVE
        ):
            self.status = self.EXPIRED
            status_changed = True

        self.full_clean()
        if status_changed and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"status"}
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.user.full_name

    @property
    def contact_phone(self):
        return self.phone or self.user.phone

    @property
    def contact_address(self):
        return self.address or self.user.address

    @property
    def is_membership_valid(self):
        role = getattr(self.user, "role", None)
        return bool(
            self.user.is_active
            and (not role or role.is_active)
            and self.status == self.ACTIVE
            and (not self.expiry_date or self.expiry_date >= timezone.localdate())
        )

    @property
    def specialized_profile(self):
        for relation in (
            "student_profile",
            "teacher_profile",
            "staff_profile",
            "librarian_profile",
        ):
            try:
                profile = getattr(self, relation)
            except ObjectDoesNotExist:
                profile = None
            if profile:
                return profile
        return None

    @property
    def specialized_profile_type(self):
        profile = self.specialized_profile
        return profile._meta.verbose_name if profile else ""

    def __str__(self):
        return f"{self.member_code} - {self.user.full_name}"


class SpecializedProfileBase(TimeStampedModel):
    expected_member_types = ()
    relation_name = ""
    identifier_field = ""

    class Meta:
        abstract = True

    def clean(self):
        errors = {}
        if not self.member_id:
            return
        if self.member.member_type not in self.expected_member_types:
            allowed = ", ".join(
                dict(Member.MEMBER_TYPE_CHOICES)[value]
                for value in self.expected_member_types
            )
            errors["member"] = f"This profile is only valid for: {allowed}."

        for relation in (
            "student_profile",
            "teacher_profile",
            "staff_profile",
            "librarian_profile",
        ):
            if relation == self.relation_name:
                continue
            try:
                other_profile = getattr(self.member, relation)
            except ObjectDoesNotExist:
                other_profile = None
            if other_profile:
                errors["member"] = "This member already has another specialized profile."
                break

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        identifier = getattr(self, self.identifier_field, "")
        if identifier:
            setattr(self, self.identifier_field, identifier.strip().upper())
        self.full_clean()
        super().save(*args, **kwargs)


class StudentProfile(SpecializedProfileBase):
    expected_member_types = (Member.STUDENT,)
    relation_name = "student_profile"
    identifier_field = "student_id"

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=120)
    program = models.CharField(max_length=120, blank=True)
    year_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    semester = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
    )
    enrollment_date = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True, validators=[phone_validator])

    class Meta:
        ordering = ["student_id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(year_level__gte=1, year_level__lte=8),
                name="student_year_level_between_1_and_8",
            ),
            models.CheckConstraint(
                condition=Q(semester__gte=1, semester__lte=3),
                name="student_semester_between_1_and_3",
            ),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.member.display_name}"


class TeacherProfile(SpecializedProfileBase):
    expected_member_types = (Member.TEACHER,)
    relation_name = "teacher_profile"
    identifier_field = "teacher_id"

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="teacher_profile")
    teacher_id = models.CharField(max_length=50, unique=True)
    faculty = models.CharField(max_length=120)
    department = models.CharField(max_length=120)
    designation = models.CharField(max_length=120, blank=True)
    office = models.CharField(max_length=120, blank=True)
    employment_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["teacher_id"]

    def __str__(self):
        return f"{self.teacher_id} - {self.member.display_name}"


class StaffProfile(SpecializedProfileBase):
    expected_member_types = (Member.STAFF,)
    relation_name = "staff_profile"
    identifier_field = "staff_id"

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="staff_profile")
    staff_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=120)
    position = models.CharField(max_length=120)
    office = models.CharField(max_length=120, blank=True)
    employment_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["staff_id"]

    def __str__(self):
        return f"{self.staff_id} - {self.member.display_name}"


class LibrarianProfile(SpecializedProfileBase):
    FULL_LIBRARIAN = Member.LIBRARIAN
    ASSISTANT = Member.ASSISTANT_LIBRARIAN

    EMPLOYEE_TYPE_CHOICES = [
        (FULL_LIBRARIAN, "Librarian"),
        (ASSISTANT, "Assistant Librarian"),
    ]
    expected_member_types = (Member.LIBRARIAN, Member.ASSISTANT_LIBRARIAN)
    relation_name = "librarian_profile"
    identifier_field = "librarian_id"

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="librarian_profile")
    librarian_id = models.CharField(max_length=50, unique=True)
    employee_type = models.CharField(max_length=30, choices=EMPLOYEE_TYPE_CHOICES)
    department = models.CharField(max_length=120, default="Library")
    shift = models.CharField(max_length=80, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    can_approve_overrides = models.BooleanField(default=False)

    class Meta:
        ordering = ["librarian_id"]

    def clean(self):
        super().clean()
        if self.member_id and self.employee_type != self.member.member_type:
            raise ValidationError(
                {"employee_type": "Employee type must match the member type."}
            )

    def __str__(self):
        return f"{self.librarian_id} - {self.member.display_name}"

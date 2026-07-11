from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Permission, Role

from .forms import MemberForm, MemberStatusForm, StudentProfileForm
from .models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile


User = get_user_model()


class MemberTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.student_role = Role.objects.get(slug=Role.STUDENT)
        cls.teacher_role = Role.objects.get(slug=Role.TEACHER)
        cls.staff_role = Role.objects.get(slug=Role.STAFF)
        cls.librarian_role = Role.objects.get(slug=Role.LIBRARIAN)

        cls.student_user = User.objects.create_user(
            username="member_student",
            email="member.student@example.com",
            password="StrongPass123!",
            first_name="Member",
            last_name="Student",
            role=cls.student_role,
        )
        cls.teacher_user = User.objects.create_user(
            username="member_teacher",
            email="member.teacher@example.com",
            password="StrongPass123!",
            first_name="Member",
            last_name="Teacher",
            role=cls.teacher_role,
        )
        cls.student_member = Member.objects.create(
            user=cls.student_user,
            member_type=Member.STUDENT,
            phone="012 345 678",
        )


class MemberModelTests(MemberTestDataMixin, TestCase):
    def test_member_code_is_generated_and_unique(self):
        teacher = Member.objects.create(
            user=self.teacher_user,
            member_type=Member.TEACHER,
        )
        self.assertRegex(self.student_member.member_code, r"^STU-\d{4}-[A-F0-9]{8}$")
        self.assertRegex(teacher.member_code, r"^TCH-\d{4}-[A-F0-9]{8}$")
        self.assertNotEqual(self.student_member.member_code, teacher.member_code)

    def test_member_type_must_match_system_role(self):
        with self.assertRaisesMessage(ValidationError, "must match"):
            Member.objects.create(
                user=self.teacher_user,
                member_type=Member.STUDENT,
            )

    def test_expired_membership_is_marked_expired(self):
        teacher = Member.objects.create(
            user=self.teacher_user,
            member_type=Member.TEACHER,
            joined_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertEqual(teacher.status, Member.EXPIRED)
        self.assertFalse(teacher.is_membership_valid)
        self.assertNotIn(teacher, Member.objects.active())

    def test_expiry_cannot_precede_joined_date(self):
        with self.assertRaisesMessage(ValidationError, "earlier than the joined date"):
            Member.objects.create(
                user=self.teacher_user,
                member_type=Member.TEACHER,
                joined_date=timezone.localdate(),
                expiry_date=timezone.localdate() - timedelta(days=1),
            )

    def test_specialized_profile_type_and_identifier_are_enforced(self):
        profile = StudentProfile.objects.create(
            member=self.student_member,
            student_id="stu-lower-001",
            department="Computer Science",
            year_level=3,
            semester=1,
        )
        self.assertEqual(profile.student_id, "STU-LOWER-001")
        self.assertEqual(self.student_member.specialized_profile, profile)

        teacher_member = Member.objects.create(
            user=self.teacher_user,
            member_type=Member.TEACHER,
        )
        with self.assertRaisesMessage(ValidationError, "only valid for"):
            StudentProfile.objects.create(
                member=teacher_member,
                student_id="INVALID-001",
                department="Science",
            )

    def test_librarian_employee_type_must_match_member_type(self):
        librarian_user = User.objects.create_user(
            username="member_librarian",
            email="member.librarian@example.com",
            password="StrongPass123!",
            role=self.librarian_role,
        )
        librarian = Member.objects.create(
            user=librarian_user,
            member_type=Member.LIBRARIAN,
        )
        with self.assertRaisesMessage(ValidationError, "must match"):
            LibrarianProfile.objects.create(
                member=librarian,
                librarian_id="LIB-001",
                employee_type=LibrarianProfile.ASSISTANT,
            )


class MemberFormTests(MemberTestDataMixin, TestCase):
    def test_member_form_excludes_users_with_existing_membership(self):
        form = MemberForm()
        self.assertNotIn(self.student_user, form.fields["user"].queryset)
        self.assertIn(self.teacher_user, form.fields["user"].queryset)

    def test_member_form_assigns_role_when_user_has_none(self):
        user = User.objects.create_user(
            username="unassigned_member",
            email="unassigned.member@example.com",
            password="StrongPass123!",
        )
        form = MemberForm(
            data={
                "user": user.pk,
                "member_type": Member.STUDENT,
                "status": Member.ACTIVE,
                "joined_date": timezone.localdate(),
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        member = form.save()
        user.refresh_from_db()
        self.assertEqual(user.role, self.student_role)
        self.assertEqual(member.user, user)

    def test_student_profile_form_only_offers_eligible_students(self):
        form = StudentProfileForm()
        self.assertIn(self.student_member, form.fields["member"].queryset)

        StudentProfile.objects.create(
            member=self.student_member,
            student_id="STU-FORM-001",
            department="Engineering",
        )
        form = StudentProfileForm()
        self.assertNotIn(self.student_member, form.fields["member"].queryset)

    def test_status_form_rejects_activation_after_expiry(self):
        self.student_member.status = Member.EXPIRED
        self.student_member.joined_date = timezone.localdate() - timedelta(days=30)
        self.student_member.expiry_date = timezone.localdate() - timedelta(days=1)
        Member.objects.filter(pk=self.student_member.pk).update(
            status=Member.EXPIRED,
            joined_date=self.student_member.joined_date,
            expiry_date=self.student_member.expiry_date,
        )
        form = MemberStatusForm(
            data={"status": Member.ACTIVE, "notes": "Attempt activation"},
            instance=self.student_member,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)


class MemberViewTests(MemberTestDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.manager_role = Role.objects.create(name="Member Manager", slug="member-manager")
        for name, codename, action in (
            ("View members", "members.view_member", "view"),
            ("Add members", "members.add_member", "add"),
            ("Edit members", "members.edit_member", "edit"),
            ("Suspend members", "members.suspend_member", "manage"),
        ):
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": Permission.MODULE_MEMBERS,
                    "action": action,
                },
            )
            cls.manager_role.permissions.add(permission)
        cls.manager = User.objects.create_user(
            username="member_manager",
            email="member.manager@example.com",
            password="StrongPass123!",
            role=cls.manager_role,
        )

    def setUp(self):
        self.client.force_login(self.manager)

    def test_member_list_search_and_filter(self):
        response = self.client.get(
            reverse("members:member_list"),
            {"q": "Member Student", "member_type": Member.STUDENT},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_member.member_code)
        self.assertContains(response, "Active")

    def test_member_detail_displays_specialized_profile(self):
        StudentProfile.objects.create(
            member=self.student_member,
            student_id="STU-DETAIL-001",
            department="Information Technology",
        )
        response = self.client.get(
            reverse("members:member_detail", kwargs={"pk": self.student_member.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "STU-DETAIL-001")
        self.assertContains(response, "Information Technology")

    def test_nested_student_profile_creation(self):
        response = self.client.post(
            reverse(
                "members:student_profile_create_for_member",
                kwargs={"member_pk": self.student_member.pk},
            ),
            {
                "member": self.student_member.pk,
                "student_id": "stu-view-001",
                "department": "Computer Science",
                "program": "BSc IT",
                "year_level": 2,
                "semester": 1,
            },
        )
        profile = StudentProfile.objects.get(member=self.student_member)
        self.assertEqual(profile.student_id, "STU-VIEW-001")
        self.assertRedirects(
            response,
            reverse("members:member_detail", kwargs={"pk": self.student_member.pk}),
        )

    def test_membership_status_can_be_suspended(self):
        response = self.client.post(
            reverse(
                "members:member_status_update",
                kwargs={"pk": self.student_member.pk},
            ),
            {"status": Member.SUSPENDED, "notes": "Temporary suspension"},
        )
        self.assertRedirects(
            response,
            reverse("members:member_detail", kwargs={"pk": self.student_member.pk}),
        )
        self.student_member.refresh_from_db()
        self.assertEqual(self.student_member.status, Member.SUSPENDED)


class MemberAPIValidationTests(MemberTestDataMixin, APITestCase):
    def test_api_rejects_profile_for_wrong_member_type(self):
        superuser = User.objects.create_superuser(
            username="member_api_admin",
            email="member.api.admin@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(superuser)
        response = self.client.post(
            "/api/teacher-profiles/",
            {
                "member": self.student_member.pk,
                "teacher_id": "TCH-INVALID-001",
                "faculty": "Science",
                "department": "Computer Science",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("member", response.data)

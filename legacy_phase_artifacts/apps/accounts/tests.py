from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import UserCreateForm, UserUpdateForm
from .models import Permission, Role


User = get_user_model()


class AccountTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.admin_role, _ = Role.objects.get_or_create(
            slug=Role.ADMIN,
            defaults={"name": "Admin", "is_system": True},
        )
        cls.student_role, _ = Role.objects.get_or_create(
            slug=Role.STUDENT,
            defaults={"name": "Student", "is_system": True},
        )
        cls.super_admin_role, _ = Role.objects.get_or_create(
            slug=Role.SUPER_ADMIN,
            defaults={"name": "Super Admin", "is_system": True},
        )
        permissions = []
        for name, codename, action in (
            ("View users", "accounts.view_user", "view"),
            ("Add users", "accounts.add_user", "add"),
            ("Edit users", "accounts.edit_user", "edit"),
            ("Deactivate users", "accounts.delete_user", "delete"),
        ):
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": Permission.MODULE_ACCOUNTS,
                    "action": action,
                },
            )
            permissions.append(permission)
        cls.admin_role.permissions.add(*permissions)

        cls.admin_user = User.objects.create_user(
            username="account_admin",
            email="account.admin@example.com",
            password="StrongPass123!",
            role=cls.admin_role,
            is_staff=True,
        )
        cls.student_user = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="StrongPass123!",
            role=cls.student_role,
        )
        cls.superuser = User.objects.create_superuser(
            username="root_user",
            email="root@example.com",
            password="StrongPass123!",
            role=cls.super_admin_role,
        )


class AccountModelTests(AccountTestDataMixin, TestCase):
    def test_email_is_normalized_when_user_is_saved(self):
        user = User.objects.create_user(
            username="mixed_email",
            email="  Mixed.Case@Example.COM  ",
            password="StrongPass123!",
            role=self.student_role,
        )
        self.assertEqual(user.email, "mixed.case@example.com")

    def test_inactive_role_has_no_permissions(self):
        self.assertTrue(self.admin_user.has_role_permission("accounts.view_user"))
        self.admin_role.is_active = False
        self.admin_role.save(update_fields=["is_active"])
        self.assertFalse(self.admin_user.has_role_permission("accounts.view_user"))
        self.assertFalse(self.admin_user.has_role(Role.ADMIN))

    def test_avatar_extension_validation(self):
        self.student_user.avatar = SimpleUploadedFile("payload.exe", b"not-an-image")
        with self.assertRaisesMessage(ValidationError, "File extension"):
            self.student_user.full_clean()


class AccountFormSecurityTests(AccountTestDataMixin, TestCase):
    def test_non_superuser_cannot_assign_protected_role(self):
        form = UserCreateForm(
            data={
                "username": "new_user",
                "email": "new.user@example.com",
                "role": self.super_admin_role.pk,
                "password1": "AnotherStrong123!",
                "password2": "AnotherStrong123!",
                "is_active": True,
            },
            actor=self.admin_user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)
        self.assertNotIn("is_staff", form.fields)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        form = UserUpdateForm(
            data={
                "username": self.student_user.username,
                "email": "ACCOUNT.ADMIN@EXAMPLE.COM",
                "role": self.student_role.pk,
                "is_active": True,
            },
            instance=self.student_user,
            actor=self.superuser,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class AuthenticationViewTests(AccountTestDataMixin, TestCase):
    def test_login_and_logout_use_post_flow(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.student_user.username, "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("catalog:book_list"))
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))

    def test_user_with_inactive_role_cannot_login(self):
        self.student_role.is_active = False
        self.student_role.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.student_user.username, "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "assigned role is inactive")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_temporary_password_must_be_changed(self):
        self.student_user.must_change_password = True
        self.student_user.save(update_fields=["must_change_password"])
        self.client.force_login(self.student_user)

        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(response, reverse("accounts:password_change"))

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "StrongPass123!",
                "new_password1": "ChangedStrong456!",
                "new_password2": "ChangedStrong456!",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.must_change_password)
        self.assertTrue(self.student_user.check_password("ChangedStrong456!"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_a_complete_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.student_user.email},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Library Management System password reset",
        )
        self.assertIn("/reset/", mail.outbox[0].body)


class UserManagementViewTests(AccountTestDataMixin, TestCase):
    def test_user_list_requires_authentication(self):
        response = self.client.get(reverse("accounts:user_list"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:user_list')}"
        self.assertRedirects(response, expected)

    def test_authorized_admin_can_view_users(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_user.username)

    def test_delegated_admin_cannot_edit_superuser(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("accounts:user_update", kwargs={"pk": self.superuser.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_deactivate_own_account(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:user_toggle_status", kwargs={"pk": self.admin_user.pk})
        )
        self.assertRedirects(
            response,
            reverse("accounts:user_detail", kwargs={"pk": self.admin_user.pk}),
        )
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

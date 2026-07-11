from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, User
from apps.activity.models import ActivityLog
from apps.announcements.models import Announcement
from apps.catalog.models import Book, BookCopy, Category
from apps.circulation.models import BorrowRecord
from apps.fines.models import Fine
from apps.members.models import Member

from .services import chart_payload, dashboard_metrics, month_range, visible_announcements


def ensure_permission(codename, module, action="view"):
    permission, _ = Permission.objects.get_or_create(
        codename=codename,
        defaults={
            "name": codename.replace(".", " ").replace("_", " ").title(),
            "module": module,
            "action": action,
        },
    )
    return permission


class DashboardServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(name="Dashboard Operator", slug="dashboard-operator")
        cls.user = User.objects.create_user(
            username="operator",
            email="operator@example.com",
            password="StrongPassword@123",
            role=cls.role,
        )
        cls.member = Member.objects.create(user=cls.user, member_type=Member.STAFF)
        cls.category = Category.objects.create(name="Computing", code="COMP")
        cls.book = Book.objects.create(
            title="Reliable Systems",
            book_code="REL-SYS-001",
            category=cls.category,
        )
        cls.copy = BookCopy.objects.create(book=cls.book, copy_code="REL-SYS-001-C1")

    def test_month_range_crosses_year_boundary_in_order(self):
        self.assertEqual(
            month_range(date(2026, 2, 14), count=4),
            [date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)],
        )

    def test_chart_payload_includes_zero_value_months_and_all_copy_statuses(self):
        payload = chart_payload(today=date(2026, 7, 2))

        self.assertEqual(len(payload["monthly"]["labels"]), 6)
        self.assertEqual(payload["monthly"]["values"], [0, 0, 0, 0, 0, 0])
        self.assertEqual(len(payload["copy_status"]["values"]), len(BookCopy.STATUS_CHOICES))
        self.assertEqual(payload["categories"]["labels"], ["Computing"])

    def test_metrics_count_overdue_without_mutating_borrow_status(self):
        today = timezone.localdate()
        self.copy.status = BookCopy.BORROWED
        self.copy.save(update_fields=["status", "updated_at"])
        borrow = BorrowRecord.objects.create(
            member=self.member,
            book_copy=self.copy,
            borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
            status=BorrowRecord.BORROWED,
        )

        metrics = dashboard_metrics(today=today)
        borrow.refresh_from_db()

        self.assertEqual(metrics["overdue_borrows"], 1)
        self.assertEqual(metrics["active_borrows"], 1)
        self.assertEqual(metrics["inventory_utilization"], 100.0)
        self.assertEqual(borrow.status, BorrowRecord.BORROWED)

    def test_metrics_calculate_only_outstanding_fine_balance(self):
        Fine.objects.create(
            member=self.member,
            amount=Decimal("12.00"),
            paid_amount=Decimal("2.00"),
            status=Fine.PARTIAL,
            reason=Fine.OTHER,
        )
        Fine.objects.create(
            member=self.member,
            amount=Decimal("5.00"),
            paid_amount=Decimal("5.00"),
            status=Fine.PAID,
            reason=Fine.OTHER,
        )

        metrics = dashboard_metrics()

        self.assertEqual(metrics["fine_balance"], Decimal("10.00"))
        self.assertEqual(metrics["outstanding_fines"], 1)

    def test_announcements_are_current_and_targeted_to_user_role(self):
        now = timezone.now()
        global_item = Announcement.objects.create(
            title="Global notice",
            content="Visible to everyone.",
            status=Announcement.PUBLISHED,
            publish_date=now - timedelta(hours=1),
        )
        targeted = Announcement.objects.create(
            title="Operator notice",
            content="Visible to operators.",
            status=Announcement.PUBLISHED,
            publish_date=now - timedelta(hours=1),
        )
        targeted.target_roles.add(self.role)
        other_role = Role.objects.create(name="Other Role", slug="other-role")
        other = Announcement.objects.create(
            title="Other notice",
            content="Not visible.",
            status=Announcement.PUBLISHED,
            publish_date=now - timedelta(hours=1),
        )
        other.target_roles.add(other_role)
        Announcement.objects.create(
            title="Expired notice",
            content="No longer visible.",
            status=Announcement.PUBLISHED,
            publish_date=now - timedelta(days=2),
            expire_date=now - timedelta(days=1),
        )

        visible = visible_announcements(self.user, now=now)

        self.assertEqual({item.pk for item in visible}, {global_item.pk, targeted.pk})


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dashboard_permission = ensure_permission(
            "dashboard.view_dashboard", "dashboard"
        )
        cls.circulation_permission = ensure_permission(
            "circulation.view_borrow", "circulation"
        )
        cls.activity_permission = ensure_permission(
            "activity.view_activity", "activity"
        )
        cls.role = Role.objects.create(name="Dashboard Viewer", slug="dashboard-viewer")
        cls.role.permissions.add(cls.dashboard_permission)
        cls.user = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="StrongPassword@123",
            role=cls.role,
        )
        cls.no_access_role = Role.objects.create(name="No Dashboard", slug="no-dashboard")
        cls.no_access_user = User.objects.create_user(
            username="noaccess",
            email="noaccess@example.com",
            password="StrongPassword@123",
            role=cls.no_access_role,
        )
        cls.member = Member.objects.create(user=cls.user, member_type=Member.STAFF)
        cls.book = Book.objects.create(title="Dashboard Book", book_code="DASH-001")
        cls.copy = BookCopy.objects.create(book=cls.book, copy_code="DASH-001-C1")
        cls.borrow = BorrowRecord.objects.create(
            member=cls.member,
            book_copy=cls.copy,
            due_date=timezone.localdate() + timedelta(days=7),
        )
        cls.activity = ActivityLog.objects.create(user=cls.user, action="Sensitive action")

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_user_without_dashboard_permission_is_redirected(self):
        self.client.force_login(self.no_access_user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_authorized_user_receives_dashboard_metrics(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")
        self.assertEqual(response.context["metrics"]["total_titles"], 1)
        self.assertContains(response, "Operational summary")

    def test_sensitive_recent_lists_require_their_own_permissions(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["recent_borrows"], [])
        self.assertEqual(response.context["recent_activities"], [])
        self.assertNotContains(response, "Sensitive action")

        self.role.permissions.add(self.circulation_permission, self.activity_permission)
        if hasattr(self.user, "_role_permission_codenames"):
            del self.user._role_permission_codenames
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["recent_borrows"][0], self.borrow)
        self.assertIn(self.activity, response.context["recent_activities"])
        self.assertContains(response, "Sensitive action")

    def test_quick_actions_are_not_rendered_without_action_permissions(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))

        self.assertNotContains(response, reverse("circulation:borrow_create"))
        self.assertNotContains(response, reverse("catalog:book_create"))


class DashboardAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.permission = ensure_permission("dashboard.view_dashboard", "dashboard")
        cls.allowed_role = Role.objects.create(name="API Dashboard", slug="api-dashboard")
        cls.allowed_role.permissions.add(cls.permission)
        cls.allowed_user = User.objects.create_user(
            username="api_dashboard",
            email="api-dashboard@example.com",
            password="StrongPassword@123",
            role=cls.allowed_role,
        )
        cls.denied_role = Role.objects.create(name="API Denied", slug="api-denied")
        cls.denied_user = User.objects.create_user(
            username="api_denied",
            email="api-denied@example.com",
            password="StrongPassword@123",
            role=cls.denied_role,
        )

    def setUp(self):
        self.client = APIClient()

    def test_dashboard_api_requires_authentication(self):
        response = self.client.get(reverse("api:dashboard"))
        self.assertEqual(response.status_code, 401)

    def test_dashboard_api_requires_dashboard_permission(self):
        self.client.force_authenticate(self.denied_user)
        response = self.client.get(reverse("api:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_api_returns_metrics_and_chart_series(self):
        self.client.force_authenticate(self.allowed_user)
        response = self.client.get(reverse("api:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_at", response.data)
        self.assertIn("metrics", response.data)
        self.assertEqual(len(response.data["charts"]["monthly"]["series"]), 6)

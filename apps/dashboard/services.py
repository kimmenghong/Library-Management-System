from calendar import month_abbr
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.activity.models import ActivityLog
from apps.announcements.models import Announcement
from apps.catalog.models import Book, BookCopy, Category
from apps.circulation.models import BorrowRecord, Reservation
from apps.fines.models import Fine
from apps.members.models import Member


ACTIVE_BORROW_STATUSES = (BorrowRecord.BORROWED, BorrowRecord.OVERDUE)
ACTIVE_RESERVATION_STATUSES = (Reservation.PENDING, Reservation.READY)


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _previous_month(value):
    if value.month == 1:
        return date(value.year - 1, 12, 1)
    return date(value.year, value.month - 1, 1)


def month_range(end_date, count=6):
    """Return ascending month starts ending in the month containing end_date."""
    months = [_month_start(end_date)]
    for _ in range(count - 1):
        months.append(_previous_month(months[-1]))
    return list(reversed(months))


def dashboard_metrics(today=None):
    """Build current operational totals without changing circulation records."""
    today = today or timezone.localdate()
    copy_counts = {
        row["status"]: row["total"]
        for row in BookCopy.objects.values("status").annotate(total=Count("id"))
    }
    active_member_filter = (
        Q(status=Member.ACTIVE, user__is_active=True)
        & (Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
        & (Q(user__role__isnull=True) | Q(user__role__is_active=True))
    )
    member_counts = Member.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=active_member_filter),
    )
    circulation_counts = BorrowRecord.objects.aggregate(
        active=Count("id", filter=Q(status__in=ACTIVE_BORROW_STATUSES)),
        overdue=Count(
            "id",
            filter=Q(status__in=ACTIVE_BORROW_STATUSES, due_date__lt=today),
        ),
        due_today=Count(
            "id",
            filter=Q(status__in=ACTIVE_BORROW_STATUSES, due_date=today),
        ),
    )
    reservation_counts = Reservation.objects.aggregate(
        active=Count("id", filter=Q(status__in=ACTIVE_RESERVATION_STATUSES)),
        ready=Count("id", filter=Q(status=Reservation.READY)),
    )
    fine_totals = Fine.objects.outstanding().aggregate(
        amount=Sum("amount"),
        paid=Sum("paid_amount"),
        count=Count("id"),
    )

    total_copies = sum(copy_counts.values())
    borrowed_copies = copy_counts.get(BookCopy.BORROWED, 0)
    return {
        "total_titles": Book.objects.count(),
        "total_copies": total_copies,
        "total_members": member_counts["total"],
        "active_members": member_counts["active"],
        "available_copies": copy_counts.get(BookCopy.AVAILABLE, 0),
        "borrowed_copies": borrowed_copies,
        "active_borrows": circulation_counts["active"],
        "overdue_borrows": circulation_counts["overdue"],
        "due_today": circulation_counts["due_today"],
        "lost_copies": copy_counts.get(BookCopy.LOST, 0),
        "damaged_copies": copy_counts.get(BookCopy.DAMAGED, 0),
        "repair_copies": copy_counts.get(BookCopy.UNDER_REPAIR, 0),
        "active_reservations": reservation_counts["active"],
        "ready_reservations": reservation_counts["ready"],
        "outstanding_fines": fine_totals["count"],
        "fine_balance": (fine_totals["amount"] or Decimal("0.00"))
        - (fine_totals["paid"] or Decimal("0.00")),
        "inventory_utilization": round(
            (borrowed_copies / total_copies * 100) if total_copies else 0,
            1,
        ),
    }


def chart_payload(today=None):
    today = today or timezone.localdate()
    months = month_range(today)
    monthly_rows = (
        BorrowRecord.objects.filter(borrow_date__gte=months[0], borrow_date__lte=today)
        .annotate(month=TruncMonth("borrow_date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    monthly_counts = {
        _month_start(row["month"]): row["total"]
        for row in monthly_rows
        if row["month"]
    }

    status_counts = {
        row["status"]: row["total"]
        for row in BookCopy.objects.values("status").annotate(total=Count("id"))
    }
    categories = list(
        Category.objects.annotate(title_count=Count("books", distinct=True))
        .filter(title_count__gt=0)
        .order_by("-title_count", "name")[:8]
    )

    monthly_labels = [f"{month_abbr[item.month]} {item.year}" for item in months]
    monthly_values = [monthly_counts.get(item, 0) for item in months]
    status_labels = [label for _, label in BookCopy.STATUS_CHOICES]
    status_values = [status_counts.get(value, 0) for value, _ in BookCopy.STATUS_CHOICES]
    category_labels = [category.name for category in categories]
    category_values = [category.title_count for category in categories]
    return {
        "monthly": {
            "labels": monthly_labels,
            "values": monthly_values,
            "series": [
                {"label": label, "value": value}
                for label, value in zip(monthly_labels, monthly_values, strict=True)
            ],
        },
        "copy_status": {
            "labels": status_labels,
            "values": status_values,
            "series": [
                {"label": label, "value": value}
                for label, value in zip(status_labels, status_values, strict=True)
            ],
        },
        "categories": {
            "labels": category_labels,
            "values": category_values,
            "series": [
                {"label": label, "value": value}
                for label, value in zip(category_labels, category_values, strict=True)
            ],
        },
    }


def most_borrowed_books(limit=5):
    return list(
        Book.objects.annotate(
            borrow_count=Count("copies__borrow_records"),
            active_borrow_count=Count(
                "copies__borrow_records",
                filter=Q(copies__borrow_records__status__in=ACTIVE_BORROW_STATUSES),
            ),
        )
        .filter(borrow_count__gt=0)
        .order_by("-borrow_count", "title")[:limit]
    )


def active_borrowers(limit=5):
    return list(
        Member.objects.select_related("user")
        .annotate(
            active_borrow_count=Count(
                "borrow_records",
                filter=Q(borrow_records__status__in=ACTIVE_BORROW_STATUSES),
            )
        )
        .filter(active_borrow_count__gt=0)
        .order_by("-active_borrow_count", "member_code")[:limit]
    )


def visible_announcements(user, now=None, limit=5):
    now = now or timezone.now()
    role_filter = Q(target_roles__isnull=True)
    if user.role_id:
        role_filter |= Q(target_roles=user.role_id)
    return list(
        Announcement.objects.filter(
            status=Announcement.PUBLISHED,
            publish_date__lte=now,
        )
        .filter(Q(expire_date__isnull=True) | Q(expire_date__gte=now))
        .filter(role_filter)
        .distinct()
        .order_by("-publish_date")[:limit]
    )


def build_dashboard_context(user, today=None, now=None):
    today = today or timezone.localdate()
    context = {
        "metrics": dashboard_metrics(today=today),
        "charts": chart_payload(today=today),
        "top_books": most_borrowed_books(),
        "active_borrowers": active_borrowers(),
        "announcements": visible_announcements(user, now=now),
        "recent_borrows": [],
        "recent_activities": [],
    }
    if user.has_role_permission("circulation.view_borrow"):
        context["recent_borrows"] = list(
            BorrowRecord.objects.select_related("member__user", "book_copy__book")
            .order_by("-created_at")[:6]
        )
    if user.has_role_permission("activity.view_activity"):
        context["recent_activities"] = list(
            ActivityLog.objects.select_related("user").order_by("-created_at")[:8]
        )
    return context

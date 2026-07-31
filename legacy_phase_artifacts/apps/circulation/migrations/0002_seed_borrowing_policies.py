from decimal import Decimal

from django.db import migrations


POLICIES = {
    "student": {
        "max_books": 3,
        "loan_period_days": 14,
        "renewal_days": 7,
        "max_renewals": 1,
        "fine_per_day": Decimal("1.00"),
        "reservation_expiry_days": 2,
    },
    "teacher": {
        "max_books": 8,
        "loan_period_days": 30,
        "renewal_days": 14,
        "max_renewals": 2,
        "fine_per_day": Decimal("1.00"),
        "reservation_expiry_days": 3,
    },
    "staff": {
        "max_books": 5,
        "loan_period_days": 21,
        "renewal_days": 7,
        "max_renewals": 1,
        "fine_per_day": Decimal("1.00"),
        "reservation_expiry_days": 2,
    },
    "librarian": {
        "max_books": 6,
        "loan_period_days": 21,
        "renewal_days": 7,
        "max_renewals": 2,
        "fine_per_day": Decimal("1.00"),
        "reservation_expiry_days": 2,
    },
    "assistant_librarian": {
        "max_books": 4,
        "loan_period_days": 14,
        "renewal_days": 7,
        "max_renewals": 1,
        "fine_per_day": Decimal("1.00"),
        "reservation_expiry_days": 2,
    },
}


def seed_policies(apps, schema_editor):
    BorrowingPolicy = apps.get_model("circulation", "BorrowingPolicy")
    for member_type, defaults in POLICIES.items():
        BorrowingPolicy.objects.get_or_create(member_type=member_type, defaults=defaults)


def unseed_policies(apps, schema_editor):
    BorrowingPolicy = apps.get_model("circulation", "BorrowingPolicy")
    BorrowingPolicy.objects.filter(member_type__in=POLICIES.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("circulation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_policies, unseed_policies),
    ]

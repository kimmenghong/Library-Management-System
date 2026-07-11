from django.db import migrations


PERMISSIONS = [
    ("View borrow records", "circulation.view_borrow", "circulation", "view"),
    ("Create borrow records", "circulation.create_borrow", "circulation", "add"),
    ("Return books", "circulation.return_book", "circulation", "manage"),
    ("Renew borrowed books", "circulation.renew_borrow", "circulation", "manage"),
    ("Manage reservations", "circulation.manage_reservation", "circulation", "manage"),
    ("Manage borrowing policies", "circulation.manage_policy", "circulation", "manage"),
    ("View fines", "fines.view_fine", "fines", "view"),
    ("Manage fines", "fines.manage_fine", "fines", "manage"),
    ("View payments", "fines.view_payment", "fines", "view"),
    ("Receive fine payments", "fines.receive_payment", "fines", "manage"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [permission[1] for permission in PERMISSIONS],
    "librarian": [
        "circulation.view_borrow",
        "circulation.create_borrow",
        "circulation.return_book",
        "circulation.renew_borrow",
        "circulation.manage_reservation",
        "fines.view_fine",
        "fines.manage_fine",
        "fines.view_payment",
        "fines.receive_payment",
    ],
    "assistant_librarian": [
        "circulation.view_borrow",
        "circulation.create_borrow",
        "circulation.return_book",
        "circulation.manage_reservation",
        "fines.view_fine",
        "fines.view_payment",
    ],
    "student": [
        "circulation.view_borrow",
        "circulation.manage_reservation",
        "fines.view_fine",
    ],
    "teacher": [
        "circulation.view_borrow",
        "circulation.manage_reservation",
        "fines.view_fine",
    ],
    "staff": [
        "circulation.view_borrow",
        "circulation.manage_reservation",
        "fines.view_fine",
    ],
}


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    permission_map = {}
    for name, codename, module, action in PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                "name": name,
                "module": module,
                "action": action,
                "is_active": True,
            },
        )
        permission_map[codename] = permission

    for slug, codenames in ROLE_PERMISSIONS.items():
        try:
            role = Role.objects.get(slug=slug)
        except Role.DoesNotExist:
            continue
        current_permissions = list(role.permissions.all())
        new_permissions = [permission_map[codename] for codename in codenames if codename in permission_map]
        role.permissions.set(current_permissions + new_permissions)


def unseed_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Permission.objects.filter(codename__in=[permission[1] for permission in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_seed_catalog_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]

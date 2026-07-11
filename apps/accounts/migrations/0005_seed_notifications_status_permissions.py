from django.db import migrations


PERMISSIONS = [
    ("View notifications", "notifications.view_notification", "notifications", "view"),
    ("Send notifications", "notifications.send_notification", "notifications", "manage"),
    ("View book status logs", "status_tracking.view_status", "status_tracking", "view"),
    ("Manage lost books", "status_tracking.manage_lost", "status_tracking", "manage"),
    ("Manage damaged books", "status_tracking.manage_damaged", "status_tracking", "manage"),
    ("Manage repair records", "status_tracking.manage_repair", "status_tracking", "manage"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [permission[1] for permission in PERMISSIONS],
    "librarian": [permission[1] for permission in PERMISSIONS],
    "assistant_librarian": [
        "notifications.view_notification",
        "status_tracking.view_status",
        "status_tracking.manage_lost",
        "status_tracking.manage_damaged",
        "status_tracking.manage_repair",
    ],
    "student": ["notifications.view_notification"],
    "teacher": ["notifications.view_notification"],
    "staff": ["notifications.view_notification"],
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
        ("accounts", "0004_seed_circulation_fines_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]

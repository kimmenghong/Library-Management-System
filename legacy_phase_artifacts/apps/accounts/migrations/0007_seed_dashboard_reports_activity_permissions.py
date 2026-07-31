from django.db import migrations


PERMISSIONS = [
    ("View dashboard", "dashboard.view_dashboard", "dashboard", "view"),
    ("View reports", "reports.view_report", "reports", "view"),
    ("Export reports", "reports.export_report", "reports", "export"),
    ("View activity logs", "activity.view_activity", "activity", "view"),
    ("View audit trail", "activity.view_audit", "activity", "view"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [permission[1] for permission in PERMISSIONS],
    "librarian": [
        "dashboard.view_dashboard",
        "reports.view_report",
        "reports.export_report",
        "activity.view_activity",
    ],
    "assistant_librarian": [
        "dashboard.view_dashboard",
        "reports.view_report",
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
        ("accounts", "0006_alter_permission_module"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]

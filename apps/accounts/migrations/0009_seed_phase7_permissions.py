from django.db import migrations


PERMISSIONS = [
    ("View digital books", "digital.view_digital_book", "digital", "view"),
    ("Manage digital books", "digital.manage_digital_book", "digital", "manage"),
    ("View reviews", "reviews.view_review", "reviews", "view"),
    ("Add reviews", "reviews.add_review", "reviews", "add"),
    ("Moderate reviews", "reviews.moderate_review", "reviews", "approve"),
    ("View announcements", "announcements.view_announcement", "announcements", "view"),
    ("Manage announcements", "announcements.manage_announcement", "announcements", "manage"),
    ("View support tickets", "support.view_ticket", "support", "view"),
    ("Add support tickets", "support.add_ticket", "support", "add"),
    ("Manage support", "support.manage_support", "support", "manage"),
    ("Manage settings", "settings.manage_settings", "settings", "manage"),
    ("Manage backups", "settings.manage_backup", "settings", "manage"),
    ("View import/export", "import_export.view_import_export", "import_export", "view"),
    ("Import data", "import_export.import_data", "import_export", "import"),
    ("Export data", "import_export.export_data", "import_export", "export"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [permission[1] for permission in PERMISSIONS],
    "librarian": [
        "digital.view_digital_book",
        "digital.manage_digital_book",
        "reviews.view_review",
        "reviews.add_review",
        "reviews.moderate_review",
        "announcements.view_announcement",
        "announcements.manage_announcement",
        "support.view_ticket",
        "support.add_ticket",
        "support.manage_support",
        "import_export.view_import_export",
        "import_export.import_data",
        "import_export.export_data",
    ],
    "assistant_librarian": [
        "digital.view_digital_book",
        "reviews.view_review",
        "reviews.add_review",
        "announcements.view_announcement",
        "support.view_ticket",
        "support.add_ticket",
        "import_export.view_import_export",
        "import_export.export_data",
    ],
    "student": [
        "digital.view_digital_book",
        "reviews.view_review",
        "reviews.add_review",
        "announcements.view_announcement",
        "support.view_ticket",
        "support.add_ticket",
    ],
    "teacher": [
        "digital.view_digital_book",
        "reviews.view_review",
        "reviews.add_review",
        "announcements.view_announcement",
        "support.view_ticket",
        "support.add_ticket",
    ],
    "staff": [
        "digital.view_digital_book",
        "reviews.view_review",
        "reviews.add_review",
        "announcements.view_announcement",
        "support.view_ticket",
        "support.add_ticket",
    ],
    "guest": [
        "announcements.view_announcement",
        "support.add_ticket",
    ],
}


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    permission_map = {}
    for name, codename, module, action in PERMISSIONS:
        permission, _ = Permission.objects.update_or_create(
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
        existing = set(role.permissions.values_list("pk", flat=True))
        additions = [permission_map[codename] for codename in codenames if codename in permission_map]
        role.permissions.add(*[permission for permission in additions if permission.pk not in existing])


def unseed_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Permission.objects.filter(codename__in=[permission[1] for permission in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_alter_permission_module"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]

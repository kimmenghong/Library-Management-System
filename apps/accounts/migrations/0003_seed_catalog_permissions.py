from django.db import migrations


PERMISSIONS = [
    ("View books", "catalog.view_book", "catalog", "view"),
    ("Add books", "catalog.add_book", "catalog", "add"),
    ("Edit books", "catalog.edit_book", "catalog", "edit"),
    ("Delete books", "catalog.delete_book", "catalog", "delete"),
    ("Manage authors", "catalog.manage_author", "catalog", "manage"),
    ("Manage publishers", "catalog.manage_publisher", "catalog", "manage"),
    ("Manage categories", "catalog.manage_category", "catalog", "manage"),
    ("Manage shelves and locations", "catalog.manage_location", "catalog", "manage"),
    ("Manage book copies", "catalog.manage_copy", "catalog", "manage"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [permission[1] for permission in PERMISSIONS],
    "librarian": [
        "catalog.view_book",
        "catalog.add_book",
        "catalog.edit_book",
        "catalog.manage_author",
        "catalog.manage_publisher",
        "catalog.manage_category",
        "catalog.manage_location",
        "catalog.manage_copy",
    ],
    "assistant_librarian": [
        "catalog.view_book",
        "catalog.manage_copy",
    ],
    "student": ["catalog.view_book"],
    "teacher": ["catalog.view_book"],
    "staff": ["catalog.view_book"],
    "guest": ["catalog.view_book"],
}


def seed_catalog_permissions(apps, schema_editor):
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
        new_permissions = [
            permission_map[codename]
            for codename in codenames
            if codename in permission_map
        ]
        role.permissions.set(current_permissions + new_permissions)


def unseed_catalog_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Permission.objects.filter(codename__in=[permission[1] for permission in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_roles_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_catalog_permissions, unseed_catalog_permissions),
    ]

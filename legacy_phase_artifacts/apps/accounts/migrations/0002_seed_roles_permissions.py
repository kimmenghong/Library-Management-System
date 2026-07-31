from django.db import migrations


PERMISSIONS = [
    ("View users", "accounts.view_user", "accounts", "view"),
    ("Add users", "accounts.add_user", "accounts", "add"),
    ("Edit users", "accounts.edit_user", "accounts", "edit"),
    ("Delete users", "accounts.delete_user", "accounts", "delete"),
    ("View roles", "accounts.view_role", "accounts", "view"),
    ("Add roles", "accounts.add_role", "accounts", "add"),
    ("Edit roles", "accounts.edit_role", "accounts", "edit"),
    ("Delete roles", "accounts.delete_role", "accounts", "delete"),
    ("View permissions", "accounts.view_permission", "accounts", "view"),
    ("Add permissions", "accounts.add_permission", "accounts", "add"),
    ("Edit permissions", "accounts.edit_permission", "accounts", "edit"),
    ("Delete permissions", "accounts.delete_permission", "accounts", "delete"),
    ("View members", "members.view_member", "members", "view"),
    ("Add members", "members.add_member", "members", "add"),
    ("Edit members", "members.edit_member", "members", "edit"),
    ("Delete members", "members.delete_member", "members", "delete"),
    ("Suspend members", "members.suspend_member", "members", "manage"),
]

ROLE_PERMISSIONS = {
    "super_admin": [permission[1] for permission in PERMISSIONS],
    "admin": [
        "accounts.view_user",
        "accounts.add_user",
        "accounts.edit_user",
        "accounts.view_role",
        "accounts.view_permission",
        "members.view_member",
        "members.add_member",
        "members.edit_member",
        "members.suspend_member",
    ],
    "librarian": [
        "members.view_member",
        "members.add_member",
        "members.edit_member",
    ],
    "assistant_librarian": [
        "members.view_member",
    ],
    "student": [],
    "teacher": [],
    "staff": [],
    "guest": [],
}

ROLE_NAMES = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "librarian": "Librarian",
    "assistant_librarian": "Assistant Librarian",
    "student": "Student",
    "teacher": "Teacher",
    "staff": "Staff",
    "guest": "Guest / Visitor",
}


def seed_roles_permissions(apps, schema_editor):
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

    for slug, name in ROLE_NAMES.items():
        role, _ = Role.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "is_system": True,
                "is_active": True,
            },
        )
        role.permissions.set(
            permission_map[codename]
            for codename in ROLE_PERMISSIONS.get(slug, [])
            if codename in permission_map
        )


def unseed_roles_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(slug__in=ROLE_NAMES.keys(), is_system=True).delete()
    Permission.objects.filter(codename__in=[permission[1] for permission in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles_permissions, unseed_roles_permissions),
    ]

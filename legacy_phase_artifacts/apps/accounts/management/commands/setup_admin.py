import os
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role


class Command(BaseCommand):
    help = "Create or update the main superuser without embedding credentials in source code."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.getenv("ADMIN_USERNAME", "admin"))
        parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL", "admin@example.com"))
        parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
        parser.add_argument(
            "--no-force-password-change",
            action="store_true",
            help="Do not require a password change after the supplied temporary password is used.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"].strip()
        email = options["email"].strip().lower()
        if not username or not email:
            raise CommandError("Both username and email are required.")

        role, _ = Role.objects.get_or_create(
            slug=Role.SUPER_ADMIN,
            defaults={
                "name": "Super Admin",
                "description": "Full system access.",
                "is_system": True,
                "is_active": True,
            },
        )
        user = User.objects.filter(username=username).first()
        created = user is None
        if created:
            user = User(username=username)

        user.email = email
        user.first_name = "System"
        user.last_name = "Administrator"
        user.role = role
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True

        password = options["password"]
        generated_password = None
        if created and not password:
            generated_password = secrets.token_urlsafe(18)
            password = generated_password
        if password:
            user.set_password(password)
            user.must_change_password = not options["no_force_password_change"]

        user.save()
        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Superuser {action}: {user.username}"))
        if generated_password:
            self.stdout.write(
                self.style.WARNING(f"Generated temporary password: {generated_password}")
            )
        elif not password and not created:
            self.stdout.write("Existing password was left unchanged.")

import getpass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.library.models import User
from apps.library.services.supabase_auth import (
    SupabaseAuthError,
    get_supabase_auth_service,
)


class Command(BaseCommand):
    help = "Verify Supabase Auth configuration and optional email/password login."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Supabase Auth email to test. The password is never printed.",
        )
        parser.add_argument(
            "--password",
            help="Supabase Auth password for non-interactive testing.",
        )
        parser.add_argument(
            "--skip-login",
            action="store_true",
            help="Only verify settings are present; do not call Supabase Auth.",
        )

    def handle(self, *args, **options):
        if not settings.USE_SUPABASE_AUTH:
            raise CommandError(
                "USE_SUPABASE_AUTH is False. Enable it in .env before testing."
            )
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise CommandError("SUPABASE_URL and SUPABASE_ANON_KEY are required.")

        self.stdout.write(self.style.SUCCESS("Supabase Auth settings found."))
        self.stdout.write(f"Project URL: {settings.SUPABASE_URL}")
        self.stdout.write(f"Default local role: {settings.SUPABASE_AUTH_DEFAULT_ROLE}")

        if options["skip_login"]:
            self.stdout.write("Skipped remote login test.")
            return

        email = options.get("email")
        if not email:
            raise CommandError("Provide --email or use --skip-login.")
        password = options.get("password") or getpass.getpass(
            "Supabase Auth password: "
        )

        try:
            identity = get_supabase_auth_service().sign_in_with_password(
                email=email,
                password=password,
            )
        except SupabaseAuthError as exc:
            raise CommandError(f"Supabase Auth login failed: {exc.message}") from exc

        local_user = User.objects.filter(email__iexact=identity.email).first()
        if not local_user:
            raise CommandError(
                "Supabase Auth login succeeded, but no matching Django users row "
                f"exists for {identity.email}."
            )
        if not local_user.is_active:
            raise CommandError("Matching Django user exists but is inactive.")
        if not local_user.role_id:
            raise CommandError("Matching Django user exists but has no role.")

        self.stdout.write(
            self.style.SUCCESS(
                "Supabase Auth login and Django users table sync check passed."
            )
        )
        self.stdout.write(f"Supabase user ID: {identity.supabase_user_id}")
        self.stdout.write(f"Django user ID: {local_user.pk}")
        self.stdout.write(f"Django role: {local_user.role.role_name}")

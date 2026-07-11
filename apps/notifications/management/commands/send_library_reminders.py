from django.core.management.base import BaseCommand, CommandError

from apps.notifications.services import (
    send_due_date_notifications,
    send_overdue_notifications,
)


class Command(BaseCommand):
    help = "Generate idempotent due-date and overdue library reminders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="Create due-date reminders for loans due within this many days (0-30).",
        )
        parser.add_argument(
            "--no-email",
            action="store_true",
            help="Create in-app notifications without sending email.",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--due-only", action="store_true")
        group.add_argument("--overdue-only", action="store_true")

    def handle(self, *args, **options):
        days = options["days"]
        if not 0 <= days <= 30:
            raise CommandError("--days must be between 0 and 30.")
        send_email = not options["no_email"]
        due = overdue = []
        if not options["overdue_only"]:
            due = send_due_date_notifications(days=days, send_email=send_email)
        if not options["due_only"]:
            overdue = send_overdue_notifications(send_email=send_email)
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(due)} due-date and {len(overdue)} overdue notification(s)."
            )
        )

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.library.models import BorrowRecord


class Command(BaseCommand):
    help = "Mark active borrow records overdue when their due date has passed."

    def handle(self, *args, **options):
        today = timezone.localdate()
        updated = BorrowRecord.objects.filter(
            status=BorrowRecord.BORROWED,
            due_date__lt=today,
            return_date__isnull=True,
        ).update(status=BorrowRecord.OVERDUE)
        self.stdout.write(
            self.style.SUCCESS(f"Overdue borrow records synchronized: {updated}")
        )

import shutil
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import BackupRecord, BackupSchedule


def create_database_backup(user=None):
    schedule = BackupSchedule.objects.first()
    backup_dir = Path(schedule.backup_directory) if schedule else Path("backups")
    if not backup_dir.is_absolute():
        backup_dir = settings.BASE_DIR / backup_dir
    backup_dir.mkdir(exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"db_backup_{timestamp}.sqlite3"
    target = backup_dir / file_name
    try:
        shutil.copy2(settings.BASE_DIR / "db.sqlite3", target)
        return BackupRecord.objects.create(
            file_name=file_name,
            file_path=str(target),
            file_size=target.stat().st_size,
            status=BackupRecord.CREATED,
            message="Database backup created successfully.",
            created_by=user,
        )
    except Exception as exc:
        return BackupRecord.objects.create(
            file_name=file_name,
            file_path=str(target),
            status=BackupRecord.FAILED,
            message=str(exc),
            created_by=user,
        )


def restore_database_backup(backup, user=None):
    source = Path(backup.file_path)
    if not source.exists():
        backup.status = BackupRecord.FAILED
        backup.message = "Backup file does not exist."
        backup.save(update_fields=["status", "message"])
        return backup
    shutil.copy2(source, settings.BASE_DIR / "db.sqlite3")
    backup.status = BackupRecord.RESTORED
    backup.message = "Database restored from this backup."
    backup.created_by = user or backup.created_by
    backup.save(update_fields=["status", "message", "created_by"])
    return backup

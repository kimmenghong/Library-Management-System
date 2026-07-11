# Phase 7: Digital Library, Engagement, Settings, Backups, and Import/Export

## Modules Added

Phase 7 completes the supporting operational modules around the core library workflow:

- Digital Library: PDF/eBook upload, validation, category management, role-restricted access, viewing, and download tracking.
- Book Reviews: member review submission, 1-5 rating validation, moderation status, moderation notes, and review history.
- Advanced Search: catalog filtering by keyword, title, ISBN, barcode, book code, author, publisher, category, shelf, availability, publication year, and language.
- Announcements: draft/published/unpublished announcements, role targeting, dashboard visibility, publish/expiry windows, and optional email delivery.
- Help & Support: FAQ management, support tickets, admin responses, and user feedback with rating validation.
- System Settings: library profile, logo/theme fields, custom system settings, borrowing policy access, email/fine/backup settings through key-value records.
- Backup & Restore: SQLite database backup creation, backup schedule settings, backup history, and restore workflow.
- Import / Export: CSV/XLSX book import and CSV/XLSX export for books, members, borrowing records, and fines.

## Database Relationships

- `DigitalBook` links to `Book`, `DigitalBookCategory`, uploaded-by `User`, and many allowed `Role` records.
- `BookReview` links each review to a `Book`, `Member`, and optional moderator `User`.
- `Announcement` links to creator `User` and many target `Role` records.
- `SupportTicket` links to the requester `User` and optional assigned staff `User`.
- `Feedback` optionally links to an authenticated `User`.
- `BackupRecord`, `ImportJob`, and `ExportJob` all store the responsible `User` for accountability.
- `SystemSetting`, `LibraryProfile`, and `BackupSchedule` provide configurable system-level records.

## Permissions

New custom permissions are seeded for:

- `digital.view_digital_book`, `digital.manage_digital_book`
- `reviews.view_review`, `reviews.add_review`, `reviews.moderate_review`
- `announcements.view_announcement`, `announcements.manage_announcement`
- `support.view_ticket`, `support.add_ticket`, `support.manage_support`
- `settings.manage_settings`, `settings.manage_backup`
- `import_export.view_import_export`, `import_export.import_data`, `import_export.export_data`

Super Admin and Admin receive all Phase 7 permissions. Librarians receive operational permissions for digital books, reviews, announcements, support, and import/export. Students, teachers, and staff receive member-facing digital, review, announcement, and support permissions.

## Business Logic

- Digital files are limited to PDF, EPUB, MOBI, AZW3, and TXT.
- Restricted digital books must specify at least one allowed role.
- Digital download access checks active status, public status, manager permissions, and role membership.
- Review ratings are validated from 1 to 5.
- Regular members can submit reviews only for their own member profile and see approved reviews plus their own history.
- Review moderation records the moderator user and moderation notes.
- Announcements respect publish date, expiry date, status, and target roles.
- Announcement emails use Django's configured email backend and mark records as sent.
- Backup creation copies the SQLite database to the configured backup directory.
- Import validates CSV/XLSX uploads and counts successful and failed rows.
- Export produces downloadable CSV or XLSX files using the existing report export service.

## Main Routes

- `/digital-library/`
- `/reviews/`
- `/announcements/`
- `/support/`
- `/settings/`
- `/import-export/`
- `/catalog/` with advanced GET filters

## Verification

Validated with:

```bash
python3 manage.py check
python3 manage.py makemigrations accounts digital_library reviews announcements support settings_app import_export
python3 manage.py migrate --noinput
```

A Django test-client smoke test also checked 37 Phase 7 pages/actions, including book import and CSV export.

# Changelog

All notable changes to the Library Management System are documented here.

## [1.0.0] - 2026-07-09

### Added

- Corrected 11-table Django implementation.
- Custom user model using the `users` table.
- Role management using the `roles` table.
- Category, author, publisher, and book management.
- Member management.
- Borrowing workflow using `borrow_records`.
- Returning workflow with `received_by` support.
- Automatic book availability update.
- Late return fine calculation.
- Fine payment tracking.
- Member notification history.
- Report generation history and CSV report files.
- Dashboard statistics.
- Django Admin configuration for all 11 active models.
- Sample data command: `python3 manage.py seed_data`.
- Automated tests for schema, relationships, borrowing, returning, fines, notifications, reports, and seed data.
- Final user, administrator, technical, database, testing, presentation, and viva documentation.
- Project health report.
- Release documentation for v1.0.0.

### Changed

- Replaced earlier multi-app prototype as the active release with one corrected app: `apps.library`.
- Updated `BorrowRecord` to use `book_id` FK to `books`, not `BookCopy`.
- Updated `BorrowRecord` to include `issued_by` and `received_by` FKs to `users`.
- Updated `Notification` to use `member_id` FK to `members`.
- Added `Report` with `generated_by` FK to `users`.
- Improved admin query performance with deeper `list_select_related`.
- Added `testserver` to local allowed hosts for Django test-client smoke checks.

### Fixed

- Data Dictionary mismatch from earlier phase-generated schema.
- Missing report table in corrected schema.
- Notification relationship target.
- Borrow record relationship target.
- Fine relationship validation.
- Local test-client host configuration.

### Known Limitations

- Reservations are not active in v1.0.0 because the lecturer's corrected Data Dictionary does not include a `reservations` table.
- Active REST API endpoints are not exposed in the corrected release.
- PDF, Excel export, barcode, QR code, email reminders, and backup dashboard are planned future enhancements.
- Older inactive phase-development folders may exist in the workspace and should be excluded or archived for strict final submission.

# Final Project Documentation

## Project Title

Library Management System

## Project Summary

The Library Management System is a complete Django web application for managing university library operations. It supports user roles, member profiles, book cataloging, copy tracking, borrowing, returns, renewals, reservations, fines, payments, notifications, digital resources, reports, analytics, support, backups, and REST API access.

## Main Objectives Covered

- Manage books, authors, publishers, categories, shelves, locations, and copies.
- Manage students, teachers, staff, librarians, and guests through role-based access.
- Track available, borrowed, lost, damaged, and repair statuses.
- Borrow, return, renew, and reserve books.
- Automatically calculate late-return fines.
- Generate reports and exports for borrowing, fines, active borrowers, and book status.
- Provide dashboard analytics for management decisions.
- Send notifications and support email workflows.
- Upload and protect digital resources.
- Expose a JWT-secured REST API for integration.
- Support backup, restore, import, and export workflows.

## User Roles

- Super Admin: full system access.
- Admin: administrative access for users, catalog, circulation, reports, and settings.
- Librarian: daily library operations.
- Assistant Librarian: limited operational support.
- Student: borrowing, reservation, notifications, reviews, digital access.
- Teacher: borrowing, reservation, notifications, reviews, digital access.
- Staff: borrowing, reservation, notifications, reviews, digital access.
- Guest / Visitor: limited read/support access.

## Core Modules

- Authentication and profile management
- User, role, and permission management
- Member and profile management
- Catalog and copy management
- Circulation: borrow, return, renew, reserve
- Fine and payment management
- Notifications and email reminders
- Lost, damaged, and repair tracking
- Dashboard, reports, and analytics
- Activity log and audit trail
- Digital library
- Reviews and ratings
- Announcements
- Help and support
- System settings
- Backup and restore
- Import and export
- REST API and JWT authentication

## Database Design Summary

The system uses normalized Django models with clear relationships:

- `User` links to `Role`.
- `Role` links to many custom `Permission` records.
- `Member` links one-to-one to `User`.
- Student, teacher, staff, and librarian profiles link one-to-one to `Member`.
- `Book` links to authors, publisher, and category.
- `BookCopy` links to book, shelf, and location.
- `BorrowRecord` links member and book copy.
- `ReturnRecord` links one-to-one with borrow record.
- `Fine` links to member and optional borrow record.
- `Payment` links to fine and member.
- `Reservation` links member and book.
- Status tracking models link to book copies and circulation records.
- Digital books link to books, categories, roles, and uploading users.

## Security Features

- Django authentication.
- Custom role-based permission system.
- JWT-secured REST API.
- CSRF protection for browser forms.
- SQL injection protection through Django ORM.
- XSS protection through Django template autoescaping.
- Secure headers and cookie settings for production.
- File upload extension and size validation.
- Environment-based secrets and deployment settings.

## Testing Summary

Automated tests cover:

- JWT login and refresh.
- API role permissions.
- API borrowing integration.
- File upload validation.
- Login by role.
- Borrowing, returning, and fine calculation.
- Reservation workflow.
- Report export.
- Admin setup command.
- Sample data command.

Run:

```bash
python3 manage.py test
```

## Deployment Summary

The project includes:

- `Dockerfile`
- `docker-compose.yml`
- `gunicorn.conf.py`
- Nginx config
- `.env.example`
- PostgreSQL-ready settings
- WhiteNoise static file support

See `docs/deployment_guide.md`.

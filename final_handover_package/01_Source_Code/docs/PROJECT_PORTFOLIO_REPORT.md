# Project Portfolio Report

Project: **Enterprise Library Management System**  
Version: **v1.0.0**  
Framework: **Python Django**  
Database: **Supabase PostgreSQL with SQLite fallback**  
Authentication: **Supabase Auth plus Django role-based access control**  
Status: **Portfolio Ready**

## 1. Professional Project Description

Enterprise Library Management System is a Django-based web application designed
to manage core university library operations in a secure, structured, and
presentation-ready way. The system supports role-based users, members, catalog
records, borrowing, returning, fine calculation, notification history, dashboard
statistics, and report generation.

The project is built around the lecturer's required 11-table Data Dictionary.
Each business table uses the required table name, primary key, and relationship
structure. Supabase PostgreSQL provides a hosted production-style database, while
Supabase Auth can handle email/password authentication. Django remains
responsible for forms, views, validation, authorization, reporting workflows, and
the local `users` table that stores role and profile data.

## 2. Portfolio Readiness

### Features List

- Supabase-ready PostgreSQL configuration
- Optional Supabase Auth login and registration
- Custom Django user model using the required `users` table
- Role-based access control for library staff and members
- Book, category, author, and publisher management
- Member management
- Borrow and return workflows
- Automatic book availability updates
- Automatic fine creation for late returns
- Fine payment status tracking
- Member notification history
- CSV report generation and report metadata
- Dashboard statistics
- Responsive Bootstrap 5 interface
- Dark/light mode
- Global search UI
- Notification dropdown
- Account/profile panel
- Professional data table controls
- Automated tests for schema, workflows, auth, seed data, and permissions

### Technology Stack

| Area | Technology |
| --- | --- |
| Backend | Python 3.14, Django 6 |
| Database | Supabase PostgreSQL, SQLite fallback |
| Authentication | Supabase Auth, Django session authentication |
| Authorization | Django custom user model and role checks |
| Frontend | Bootstrap 5, HTML, CSS, JavaScript |
| Static files | WhiteNoise compressed manifest storage |
| Reports | Django file storage, CSV generation |
| Testing | Django tests, Flake8, Black, isort |
| Deployment | Environment variables, Gunicorn-ready settings |

### Architecture Overview

```text
User Browser
  |
  v
Django Templates + Bootstrap UI
  |
  v
Django Views, Forms, Validation, Role Checks
  |
  v
Django ORM
  |
  v
Supabase PostgreSQL

Supabase Auth verifies email/password identity.
Django users and roles control application authorization.
```

### Folder Structure Diagram

```text
Library Management System/
|-- apps/library/              Active corrected 11-table Django app
|-- apps/library/services/     Supabase Auth integration helper
|-- apps/library/management/   Seed data and verification commands
|-- config/                    Django settings, URL routing, ASGI/WSGI
|-- templates/library/         Active server-rendered UI templates
|-- static/                    CSS, JavaScript, logo, favicon, login image
|-- staticfiles/               Collected static files for production
|-- media/                     Generated report files
|-- docs/                      Portfolio, release, demo, and submission docs
|-- requirements.txt           Runtime dependencies
|-- .env.example               Safe environment template
`-- README.md                  Portfolio-ready project guide
```

## 3. Project Documentation

### System Requirements

- Python 3.14 or a compatible Python 3 version supported by Django 6
- pip and virtual environment support
- Supabase project for hosted PostgreSQL and optional Supabase Auth
- Modern browser for the Bootstrap interface

### Database Requirements

For Supabase PostgreSQL:

- Database host
- Database name
- Database username
- Database password
- SSL mode set to `require`

For local fallback:

- SQLite database file configured through `SQLITE_NAME`

### Environment Variables

Required production variables:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DATABASE_ENGINE
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
DATABASE_HOST
DATABASE_PORT
DATABASE_SSLMODE
SUPABASE_URL
SUPABASE_ANON_KEY
USE_SUPABASE_AUTH
CSRF_TRUSTED_ORIGINS
```

### Deployment Requirements

- `DJANGO_DEBUG=False`
- Strong secret key
- Valid allowed hosts
- HTTPS-ready security settings
- Production database
- `collectstatic` completed
- Static files served by WhiteNoise, Nginx, or equivalent
- Database and media backup strategy

### Known Limitations

- The active portfolio release intentionally keeps the 11-table lecturer schema,
  so extra business modules that require extra tables are not active.
- Public REST API documentation is not exposed in the active corrected release.
- Supabase Auth requires internet access and valid Supabase credentials.
- Screenshots should be added manually before publishing the GitHub repository.

### Future Enhancements

- REST API and OpenAPI documentation
- Barcode and QR-code scanning
- Real-time notifications
- Scheduled email reminders
- Advanced analytics charts
- Cloud object storage for reports
- CI/CD deployment pipeline
- Dedicated mobile application

## 4. Data Dictionary Compliance

The active app complies with the 11 required business tables:

```text
roles
users
categories
authors
publishers
books
members
borrow_records
fines
notifications
reports
```

Primary keys:

```text
role_id
user_id
category_id
author_id
publisher_id
book_id
member_id
borrow_id
fine_id
notification_id
report_id
```

No database schema changes were made during portfolio preparation.

## 5. Code Review Summary

### Django Best Practices

- Uses a custom Django user model for the required `users` table.
- Uses Django ORM relationships instead of raw SQL for application workflows.
- Uses forms and validation for user input.
- Uses decorators and role checks for protected staff workflows.
- Uses `select_related()` for key relationship-heavy queries.
- Uses database indexes and constraints in the active models.
- Uses environment variables for sensitive configuration.
- Uses WhiteNoise manifest static storage for production-style static files.

### Naming Conventions

- Active models use clear singular class names: `Role`, `User`, `Book`,
  `Member`, `BorrowRecord`, `Fine`, `Notification`, and `Report`.
- Table names use exact `db_table` values required by the lecturer.
- Primary key fields use the exact lecturer-required names.
- Template names are grouped under `templates/library/`.

### Quality Checks

Latest local audit:

```text
python manage.py check: passed
python manage.py makemigrations --check --dry-run: passed
python manage.py migrate --check: passed
python manage.py test: 22 tests passed
flake8 apps/library config: passed
isort check: passed
black check: passed
node --check static/js/main.js: passed
```

### Unused Files Note

Older phase folders remain in the workspace as development artifacts. They are
excluded from active formatting configuration and are not installed in
`INSTALLED_APPS`. For a public portfolio repository, they can be archived in a
separate branch or removed after confirming they are not needed for submission.

## 6. Portfolio Assets

### Short Project Summary - 100 Words

Enterprise Library Management System is a Django web application for managing university library operations. It includes role-based users, members, books, borrowing, returns, automatic fines, notifications, dashboard statistics, and report generation. The project uses Supabase PostgreSQL for a hosted production-style database and optional Supabase Auth for email/password authentication, while Django keeps the required users table for roles and profiles. The active schema follows the lecturer's 11-table Data Dictionary exactly. A responsive Bootstrap interface, dark/light mode, global search, professional tables, and automated tests make the system suitable for university submission and software portfolio presentation today for confident classroom demos and recruiter interviews.

### Detailed Project Description - About 500 Words

Enterprise Library Management System is a full-stack Django project created to
solve common university library management problems such as manual book tracking,
unorganized member records, borrowing mistakes, late return fine calculation,
and limited reporting. The system provides a structured web interface for
library staff and members while preserving a clear, normalized database design.

The backend is built with Python Django, using Django's forms, views, ORM,
custom user model, authentication integration, and admin support. The active
business schema follows the lecturer's 11-table Data Dictionary exactly:
`roles`, `users`, `categories`, `authors`, `publishers`, `books`, `members`,
`borrow_records`, `fines`, `notifications`, and `reports`. Each table uses the
required table name and primary key name, and the relationships are implemented
with Django foreign keys. For example, borrow records connect members, books,
the issuing user, and the receiving user. Fines connect to borrow records and
members. Notifications connect to members, and reports connect to the user who
generated them.

The project is configured for Supabase PostgreSQL, which provides a hosted
database suitable for demonstration and deployment. Supabase Auth can be used
for email/password authentication, while Django keeps the local `users` table
for profile data, status, and role-based authorization. This separation makes
the system easier to explain: Supabase verifies identity, and Django controls
what each user can access inside the library application.

The system includes practical library workflows. Staff can manage books,
authors, publishers, categories, members, fines, notifications, and reports.
During borrowing, the system creates a borrow record and updates book
availability. During return, the system records the receiving user, updates the
book stock, and creates a fine automatically if the return is late. Reports
store generated report metadata and optional report files.

The frontend uses Bootstrap 5, custom CSS, and JavaScript to provide a
portfolio-ready user interface. It includes a professional login page with a
library image, dashboard statistic cards, sidebar navigation, topbar global
search, notification center, account panel, dark/light mode, responsive layout,
and enhanced data tables with sorting, filters, export-style downloads, and
print actions. Static files are managed with WhiteNoise and production-style
manifest storage.

The project also includes a repeatable sample data command and automated tests.
The test suite verifies the required table structure, relationships, borrowing
workflow, return workflow, fine calculation, notification creation, report
generation, seed data, authentication behavior, and role-based access control.
This makes the project useful not only as a university final project but also as
a professional portfolio example demonstrating backend architecture, database
design, UI polish, security awareness, testing, and deployment preparation.

### Resume-Ready Bullet Points

- Built a full-stack Django Library Management System with Supabase PostgreSQL,
  custom user model, role-based access control, and Bootstrap 5 UI.
- Implemented an academic 11-table Data Dictionary with exact primary keys,
  foreign keys, constraints, indexes, and Django ORM relationships.
- Developed borrowing, returning, automatic fine calculation, notification, and
  report generation workflows with automated tests.
- Integrated optional Supabase Auth for email/password authentication while
  preserving Django-managed role and profile data.
- Improved the frontend with responsive dashboards, dark/light mode, global
  search, notification center, profile panel, and professional data tables.
- Verified quality with Django checks, migration checks, Flake8, Black, isort,
  JavaScript syntax checks, and a passing 22-test suite.

### LinkedIn Project Description

I completed an Enterprise Library Management System using Python Django,
Supabase PostgreSQL, Supabase Auth, Bootstrap 5, and JavaScript. The project
supports role-based access, catalog management, member management, borrowing and
returning workflows, automatic fine calculation, notifications, dashboard
statistics, and report generation. A major focus was database correctness: the
active schema follows an 11-table academic Data Dictionary exactly, including
required table names, primary keys, and foreign key relationships. I also
polished the UI for portfolio presentation with dark/light mode, global search,
responsive layout, notification center, profile panel, and enhanced tables. The
project includes seed data, deployment-ready settings, and automated tests for
core workflows.

## 7. Deployment Preparation

### Production Settings Review

- Uses environment variables through `.env`
- Blocks placeholder Supabase values when Supabase Auth is enabled
- Supports PostgreSQL SSL mode
- Supports secure cookies and HTTPS settings
- Uses WhiteNoise compressed manifest storage
- Provides configurable email settings
- Provides configurable upload limits

### Static Files

Static source:

```text
static/
```

Collected output:

```text
staticfiles/
```

Production command:

```bash
python manage.py collectstatic --noinput
```

### Media Files

Media root:

```text
media/
```

Report files are stored under:

```text
media/reports/
```

Back up media files before deployment or migration.

### Security Checklist

- Do not commit `.env`
- Rotate any exposed credentials
- Use HTTPS in production
- Set `DJANGO_DEBUG=False`
- Set secure cookies
- Configure `CSRF_TRUSTED_ORIGINS`
- Use strong Supabase database password
- Use least-privilege deployment credentials where possible
- Back up Supabase data before major changes

## 8. Final Verification

Portfolio preparation did not modify:

- Database models
- Migrations
- Lecturer 11-table schema
- Supabase Auth service
- Borrowing, return, fine, notification, or report business logic

Verification commands:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python manage.py test
python -m flake8 apps/library config --exclude apps/library/migrations
python -m isort --check-only apps/library config --skip apps/library/migrations
python -m black --check apps/library config --exclude 'apps/library/migrations'
node --check static/js/main.js
```

## 9. Production Readiness Rating

| Area | Rating | Notes |
| --- | --- | --- |
| Database design | High | Correct 11-table schema with relationships |
| Backend workflows | High | Core library workflows covered by tests |
| Authentication | High | Supabase-ready and Django role-aware |
| UI/UX | High | Responsive, branded, and demo-ready |
| Testing | High | 22 automated tests passing |
| Deployment readiness | Medium-High | Needs real production host and secrets |
| API readiness | Medium | API docs are not active in corrected release |

Estimated production readiness: **88%**

## 10. Final Portfolio Statement

This project is strong as a software portfolio piece because it demonstrates
database modeling, Django backend development, authentication integration,
role-based access, real workflow implementation, automated testing, UI polish,
and deployment awareness. It is also easy to explain in interviews because the
architecture separates authentication, authorization, business workflow, and
database design clearly.

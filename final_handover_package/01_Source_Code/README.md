# Enterprise Library Management System

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-success.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ecf8e.svg)](https://supabase.com/)
[![Auth](https://img.shields.io/badge/Auth-Supabase%20Auth-3ecf8e.svg)](https://supabase.com/auth)
[![Frontend](https://img.shields.io/badge/UI-Bootstrap%205-7952b3.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Version: **v1.0.0**  
Status: **Portfolio Ready / University Final Project**  
Backend: **Python Django**  
Database: **Supabase PostgreSQL with SQLite fallback for local development**

## Project Description

Enterprise Library Management System is a professional Django web application
for managing university library operations. It supports role-based access,
catalog management, member management, borrowing and returning workflows,
automatic fine calculation, notifications, dashboard analytics, CSV report
generation, and a polished Bootstrap 5 interface.

The final active release follows the lecturer's required 11-table business
Data Dictionary exactly. Supabase PostgreSQL is used as the hosted database,
Supabase Auth can handle email/password authentication, and Django keeps the
local `users` table for role, profile, and authorization data.

## Portfolio Highlights

- Corrected 11-table academic data model with exact table and primary-key names.
- Custom Django user model mapped to the required `users` table.
- Supabase PostgreSQL integration with SSL-ready settings.
- Optional Supabase Auth login/register flow that preserves Django role control.
- Role-based access for admin, librarian, assistant librarian, student, teacher,
  staff, and visitor-style access.
- Complete borrowing, returning, fine, notification, and reporting workflows.
- Responsive professional UI with dashboard cards, dark/light mode, global search,
  notification center, account panel, table sorting, filtering, print, and export
  controls.
- Automated tests covering schema compliance, authentication, borrowing, return,
  fine calculation, notifications, reporting, seed data, and role permissions.

## Features

### Administration

- User and role management
- Member management
- Category, author, publisher, and book management
- Dashboard statistics
- Report generation and report history

### Circulation

- Borrow book workflow
- Return book workflow
- Automatic stock updates
- Overdue detection
- Automatic fine creation for late returns

### Member Services

- Book search and filtering
- Member notification history
- Fine status visibility
- Role-aware access control

### User Experience

- Bootstrap 5 responsive layout
- Library login background image
- Sidebar and top navigation
- Dark/light mode stored in `localStorage`
- Global module search
- Profile/account panel
- Notification dropdown
- Professional tables with sorting, column filters, export, and print actions
- Logo, favicon, footer, and version branding

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.14, Django 6 |
| Database | Supabase PostgreSQL, SQLite fallback |
| Authentication | Supabase Auth plus Django session login |
| Authorization | Django role-based access control |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Static Files | WhiteNoise, compressed manifest storage |
| Reports | CSV report generation |
| Testing | Django test framework, Flake8, Black, isort |
| Deployment | Gunicorn, WhiteNoise, environment variables |

## Architecture Overview

```text
Browser
  |
  | HTML, CSS, Bootstrap, JavaScript
  v
Django Views and Forms
  |
  | Role checks, validation, workflow logic
  v
Django ORM
  |
  | SQL over SSL
  v
Supabase PostgreSQL

Supabase Auth
  |
  | Email/password authentication
  v
Django users table
  |
  | role_id, profile, status, permissions
  v
Role-based library access
```

## Final Data Dictionary Compliance

The active Library Management System business schema contains exactly these
11 lecturer-required tables:

| Table | Primary Key | Purpose |
| --- | --- | --- |
| `roles` | `role_id` | User access roles |
| `users` | `user_id` | System users and profile data |
| `categories` | `category_id` | Book categories |
| `authors` | `author_id` | Book authors |
| `publishers` | `publisher_id` | Book publishers |
| `books` | `book_id` | Catalog and stock records |
| `members` | `member_id` | Library member records |
| `borrow_records` | `borrow_id` | Borrow and return transactions |
| `fines` | `fine_id` | Fine and payment status records |
| `notifications` | `notification_id` | Member notification history |
| `reports` | `report_id` | Generated report metadata |

Important relationships:

- `users.role_id` references `roles.role_id`
- `books.category_id` references `categories.category_id`
- `books.author_id` references `authors.author_id`
- `books.publisher_id` references `publishers.publisher_id`
- `members.user_id` references `users.user_id`
- `borrow_records.member_id` references `members.member_id`
- `borrow_records.book_id` references `books.book_id`
- `borrow_records.issued_by` references `users.user_id`
- `borrow_records.received_by` references `users.user_id`
- `fines.borrow_id` references `borrow_records.borrow_id`
- `fines.member_id` references `members.member_id`
- `notifications.member_id` references `members.member_id`
- `reports.generated_by` references `users.user_id`

Django framework tables such as sessions, migrations, content types, and admin
logs may exist because Django requires them. They are not additional business
Data Dictionary tables.

## Folder Structure

```text
Library Management System/
|-- apps/
|   `-- library/
|       |-- management/commands/
|       |   |-- seed_data.py
|       |   `-- verify_supabase_auth.py
|       |-- migrations/
|       |-- admin.py
|       |-- apps.py
|       |-- forms.py
|       |-- models.py
|       |-- services/
|       |   `-- supabase_auth.py
|       |-- signals.py
|       |-- tests.py
|       |-- urls.py
|       `-- views.py
|-- config/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- templates/
|   `-- library/
|-- static/
|   |-- css/
|   |-- images/
|   `-- js/
|-- media/
|-- docs/
|-- requirements.txt
|-- .env.example
|-- Dockerfile
|-- docker-compose.yml
|-- manage.py
`-- README.md
```

Note: older phase folders may remain in the workspace as development artifacts,
but the active installed app for the corrected portfolio release is
`apps.library.apps.LibraryConfig`.

## Screenshots

Add project screenshots before publishing the repository:

```text
docs/screenshots/login-page.png
docs/screenshots/dashboard.png
docs/screenshots/books-table.png
docs/screenshots/borrow-flow.png
docs/screenshots/fines.png
docs/screenshots/reports.png
docs/screenshots/supabase-tables.png
docs/screenshots/mobile-layout.png
```

Suggested GitHub README layout:

| Login | Dashboard |
| --- | --- |
| Add screenshot | Add screenshot |

| Books | Borrowing |
| --- | --- |
| Add screenshot | Add screenshot |

## System Requirements

- macOS, Linux, or Windows
- Python 3.14 or compatible Python 3.x version supported by Django 6
- pip and virtual environment support
- Supabase project for hosted PostgreSQL and optional Supabase Auth
- PostgreSQL connection credentials when `DATABASE_ENGINE=postgresql`

## Installation

```bash
git clone https://github.com/<your-username>/enterprise-library-management-system.git
cd enterprise-library-management-system

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Update `.env` before running the project.

## Environment Variables

Core variables:

```text
DJANGO_SECRET_KEY=change-this-secret-key-before-deployment
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,testserver

DATABASE_ENGINE=sqlite
SQLITE_NAME=library.sqlite3
```

Supabase PostgreSQL example:

```text
DATABASE_ENGINE=postgresql
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=copy-your-supabase-database-password
DATABASE_HOST=db.<project-ref>.supabase.co
DATABASE_PORT=5432
DATABASE_SSLMODE=require
```

Supabase Auth example:

```text
USE_SUPABASE_AUTH=True
SUPABASE_PROJECT_REF=<project-ref>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=copy-your-supabase-anon-key
SUPABASE_AUTH_DEFAULT_ROLE=Student
SUPABASE_AUTH_REQUIRE_LOCAL_USER=True
```

Never commit real `.env` secrets to GitHub.

## Database Setup

Run migrations:

```bash
python manage.py migrate
```

Verify no pending model changes:

```bash
python manage.py makemigrations --check --dry-run
```

Load sample data:

```bash
python manage.py seed_data
```

Create a superuser:

```bash
python manage.py createsuperuser
```

## Running The Project

```bash
python manage.py runserver 127.0.0.1:8000
```

If your environment blocks the auto-reloader:

```bash
python manage.py runserver 127.0.0.1:8000 --noreload
```

Open:

```text
http://127.0.0.1:8000/
```

## Demo Accounts

After running `python manage.py seed_data`, sample accounts are created for
testing and demonstration. Use placeholders in public documentation instead of
publishing real passwords:

| Username | Role |
| --- | --- |
| `sample_admin` | Super Admin |
| `sample_librarian` | Librarian |
| `sample_assistant` | Assistant Librarian |
| `sample_student` | Student |
| `sample_teacher` | Teacher |
| `sample_staff` | Staff |

Password: `[DEMO_PASSWORD_FROM_LOCAL_SEED_DATA]`

## Testing And Quality

Run the complete verification suite:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python manage.py test
python -m flake8 apps/library config --exclude apps/library/migrations
python -m isort --check-only apps/library config --skip apps/library/migrations
python -m black --check apps/library config --exclude 'apps/library/migrations'
```

Current portfolio audit result:

```text
Django system check: passed
Migration check: passed
Automated tests: 22 passed
Flake8: passed
isort: passed
Black: passed
JavaScript syntax check: passed
```

## API Documentation

The corrected 11-table portfolio release focuses on server-rendered Django
workflows. Public API routes and Swagger documentation are not exposed in the
active installed app. API endpoints can be added later as a separate enhancement
without changing the 11-table business schema.

## Deployment Preparation

Production checklist:

- Set `DJANGO_DEBUG=False`
- Set a strong `DJANGO_SECRET_KEY`
- Configure `DJANGO_ALLOWED_HOSTS`
- Use Supabase PostgreSQL or another production PostgreSQL database
- Keep `DATABASE_SSLMODE=require` for Supabase
- Run `python manage.py collectstatic --noinput`
- Serve static files with WhiteNoise or a production web server
- Configure `CSRF_TRUSTED_ORIGINS`
- Enable secure cookies and HTTPS settings
- Back up database and media files
- Store all secrets in environment variables

Suggested production commands:

```bash
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

## Known Limitations

- The active release intentionally follows the lecturer's 11-table schema, so
  modules requiring extra business tables are documented as future work.
- API documentation is not exposed in the active corrected release.
- Email delivery uses configurable Django email settings and may require SMTP
  credentials in production.
- Supabase Auth requires internet access and valid Supabase credentials.
- Browser screenshots should be added manually before publishing the portfolio.

## Future Enhancements

- REST API and OpenAPI documentation for all major workflows
- Barcode and QR-code scanning
- Real-time dashboard updates
- Email reminder scheduling
- Advanced analytics charts
- Dedicated mobile app
- Cloud file storage for generated reports and media
- CI/CD deployment to a production hosting platform

## Documentation

- [Project Portfolio Report](docs/PROJECT_PORTFOLIO_REPORT.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Final Project Documentation](docs/final_project_documentation.md)
- [Final Submission Package](docs/final_submission_package/README.md)
- [Project Health Report](docs/project_health_report_11_table_audit.md)
- [Release Notes v1.0.0](docs/release/v1.0.0.md)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

# Technical Documentation

Project: Enterprise Library Management System  
Framework: Python Django  
Database: SQLite for development  
Version: Corrected 11-table implementation

## 1. System Architecture

The system follows Django's Model-Template-View architecture.

```text
Browser
  |
  v
Django URL Router
  |
  v
Views in apps.library.views
  |
  +-- Forms in apps.library.forms
  +-- Models in apps.library.models
  |
  v
Templates in templates/library
  |
  v
SQLite database
```

### 1.1 Main Layers

| Layer | Responsibility |
| --- | --- |
| Models | Define database tables, fields, relationships, validation, and constraints |
| Forms | Validate user input and generate Bootstrap-friendly form widgets |
| Views | Handle requests, permissions, business workflow, and responses |
| Templates | Render HTML pages using Bootstrap |
| Admin | Provide Django Admin management for the 11 models |
| Tests | Verify schema, relationships, workflows, sample data, and report generation |

## 2. Database Design

The database follows the lecturer's required 11 application tables:

1. `roles`
2. `users`
3. `categories`
4. `authors`
5. `publishers`
6. `books`
7. `members`
8. `borrow_records`
9. `fines`
10. `notifications`
11. `reports`

Django framework support tables may also exist. They are not part of the Library Management System Data Dictionary.

## 3. ER Diagram

Text-based ER diagram:

```text
roles (role_id)
  1 ---- * users (user_id, role_id)
             |
             | 1
             |
             1 members (member_id, user_id)
                    |
                    | 1
                    |
                    * borrow_records (borrow_id, member_id, book_id, issued_by, received_by)
                         |                              |
                         |                              |
                         * fines (fine_id, borrow_id)   |
                                                        |
books (book_id) ----------------------------------------+
  |
  +-- category_id -> categories (category_id)
  +-- author_id -> authors (author_id)
  +-- publisher_id -> publishers (publisher_id)

members (member_id)
  1 ---- * notifications (notification_id, member_id)

users (user_id)
  1 ---- * reports (report_id, generated_by)
```

## 4. Django Apps

### 4.1 Active App

The corrected active system uses:

```text
apps.library
```

This app contains:

- `models.py`
- `forms.py`
- `views.py`
- `urls.py`
- `admin.py`
- `tests.py`
- `test_runner.py`
- `management/commands/seed_data.py`
- `migrations/0001_initial.py`

### 4.2 Inactive Legacy Apps

Earlier phase-generation folders may exist in the workspace, but they are not installed in `config/settings.py`.

The active `INSTALLED_APPS` contains:

```text
django.contrib.admin
django.contrib.auth
django.contrib.contenttypes
django.contrib.sessions
django.contrib.messages
django.contrib.staticfiles
apps.library.apps.LibraryConfig
```

For strict submission, inactive legacy apps should be excluded or archived.

## 5. API Overview

The corrected final 11-table implementation does not expose active API endpoints.

Reason:

- The lecturer required exactly 11 application tables.
- Earlier API code was based on the larger multi-app prototype.
- The active corrected system uses normal Django views and templates.

Future API enhancement:

- API endpoints can be rebuilt later using Django REST Framework against the corrected `apps.library` models only.

Suggested future API endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/api/books/` | List and manage books |
| `/api/members/` | List and manage members |
| `/api/borrow-records/` | Manage borrow records |
| `/api/fines/` | Manage fines |
| `/api/notifications/` | Manage notifications |
| `/api/reports/` | Manage report history |

## 6. Folder Structure

Recommended final submission structure:

```text
Library Management System/
|-- apps/
|   |-- library/
|   |   |-- management/
|   |   |   `-- commands/
|   |   |       `-- seed_data.py
|   |   |-- migrations/
|   |   |   |-- 0001_initial.py
|   |   |   `-- __init__.py
|   |   |-- __init__.py
|   |   |-- admin.py
|   |   |-- apps.py
|   |   |-- forms.py
|   |   |-- models.py
|   |   |-- test_runner.py
|   |   |-- tests.py
|   |   |-- urls.py
|   |   `-- views.py
|   `-- __init__.py
|-- config/
|   |-- __init__.py
|   |-- asgi.py
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- docs/
|   `-- final_submission_package/
|-- static/
|   |-- css/
|   |   `-- style.css
|   `-- js/
|       `-- main.js
|-- templates/
|   `-- library/
|       |-- base.html
|       |-- login.html
|       |-- dashboard.html
|       |-- book_list.html
|       |-- borrow_form.html
|       |-- borrow_list.html
|       |-- return_form.html
|       |-- fine_list.html
|       |-- fine_payment_form.html
|       |-- notification_list.html
|       |-- report_list.html
|       |-- entity_list.html
|       |-- entity_form.html
|       `-- confirm_delete.html
|-- .env.example
|-- manage.py
|-- README.md
`-- requirements.txt
```

## 7. Core Workflows

### 7.1 Authentication

1. User submits username and password.
2. Django authenticates against custom `users` table.
3. If valid, the user is redirected to dashboard.
4. If invalid, login error is displayed.

### 7.2 Borrow Book

1. Staff selects member and book.
2. System validates member is active.
3. System validates book is available.
4. System creates `borrow_records` row.
5. System stores logged-in staff user as `issued_by`.
6. System decreases book `available_quantity`.
7. System updates book status if needed.

### 7.3 Return Book

1. Staff opens active borrow record.
2. Staff enters return date.
3. System validates return date.
4. System stores logged-in staff user as `received_by`.
5. System changes borrow status to Returned.
6. System increases book `available_quantity`.
7. System calculates fine if overdue.
8. System creates member notification if fine is created.

### 7.4 Report Generation

1. Staff selects report type.
2. System creates `reports` row.
3. System stores logged-in staff user as `generated_by`.
4. System creates CSV file if no file was uploaded.

## 8. Deployment Guide

### 8.1 Development Deployment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py seed_data
python3 manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

### 8.2 Production Checklist

Before production:

1. Set `DJANGO_DEBUG=False`.
2. Set a strong `DJANGO_SECRET_KEY`.
3. Set correct `DJANGO_ALLOWED_HOSTS`.
4. Enable secure cookies.
5. Enable HTTPS redirect.
6. Configure static file serving.
7. Use Gunicorn or another WSGI server.
8. Use Nginx as reverse proxy if deploying on Linux server.
9. Use PostgreSQL or MySQL if required.
10. Back up database and media.

### 8.3 Production Commands

```bash
python3 manage.py migrate
python3 manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

## 9. Technical Risks And Mitigation

| Risk | Mitigation |
| --- | --- |
| Accidental schema drift | Use `makemigrations --check --dry-run` |
| Broken relationships | Use model tests and database integrity checks |
| Inactive legacy app confusion | Submit only corrected app or archive old folders |
| Weak production settings | Use secure `.env` values |
| Large list performance | Add pagination and indexes in future |
| Data loss | Back up SQLite database and media folder |

## 10. Technical Conclusion

The corrected system is technically stable for university final project submission. It uses a clear Django architecture, follows the lecturer's 11-table Data Dictionary, validates important business rules, includes automated tests, and provides complete documentation for users, administrators, and examiners.

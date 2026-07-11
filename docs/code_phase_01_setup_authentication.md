# Code Phase 1: Project Setup and Authentication

## Scope

This code phase provides the Django project bootstrap and the complete server-rendered authentication and user authorization foundation. It uses Django's custom user model from the first migration and keeps library roles separate from Django's framework permissions.

## Source Layout

```text
Library Management System/
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   └── accounts/
│       ├── management/commands/setup_admin.py
│       ├── migrations/
│       ├── templatetags/account_tags.py
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── decorators.py
│       ├── forms.py
│       ├── middleware.py
│       ├── mixins.py
│       ├── models.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
├── templates/
│   ├── accounts/
│   ├── includes/
│   ├── registration/
│   └── base.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Authentication Features

- Username and password login with active-user and active-role validation
- POST-only logout
- Email password reset with expiring signed tokens
- Authenticated password change
- Mandatory password change for temporary credentials
- Case-insensitive email validation and normalized email storage
- Self-service profile editing with avatar size and extension validation
- User, role, and custom permission management
- Protected Super Admin and Admin roles
- Role-aware navigation and reusable view/decorator authorization checks
- Login/logout/failure activity logging and redacted password audit data

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py setup_admin --username admin --email admin@example.com
python manage.py runserver
```

The setup command generates a temporary password when a new password is not provided. For automation, set `ADMIN_PASSWORD` in the process environment instead of committing it to source control.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.accounts
```

# Phase 8: REST API, Security, Testing, Deployment, and Final Setup

## REST API Setup

Phase 8 adds a dedicated `apps.api` Django app using Django REST Framework.

Main files:

- `apps/api/serializers.py`
- `apps/api/views.py`
- `apps/api/permissions.py`
- `apps/api/auth.py`
- `apps/api/urls.py`
- `apps/api/tests.py`

The API is mounted at:

```text
/api/
```

JWT authentication routes:

```text
/api/auth/token/
/api/auth/token/refresh/
/api/auth/token/verify/
```

## API Endpoint Coverage

The router exposes endpoints for:

- Users, roles, permissions
- Members and student/teacher/staff/librarian profiles
- Books, book copies, authors, publishers, categories, shelves, locations
- Borrow records, return records, renewals, reservations, borrowing policies
- Fines and payments
- Notifications and email reminders
- Book status logs, lost books, damaged books, repair records
- Digital books and digital categories
- Reviews and ratings
- Announcements
- FAQ, support tickets, feedback
- Library profile, system settings, backup schedules, backup records
- Import jobs and export jobs
- Activity logs and audit logs

## JWT Authentication

JWT is provided by `djangorestframework-simplejwt`.

The login response includes:

- `access`
- `refresh`
- user ID
- username
- email
- full name
- role slug

API requests use:

```http
Authorization: Bearer <access-token>
```

## API Permissions By Role

`apps/api/permissions.py` maps DRF actions to the custom role permission system.

Examples:

- `GET /api/books/` requires `catalog.view_book`
- `POST /api/books/` requires `catalog.add_book`
- `PATCH /api/books/{id}/` requires `catalog.edit_book`
- `DELETE /api/books/{id}/` requires `catalog.delete_book`
- `POST /api/borrow-records/` requires `circulation.create_borrow`
- `POST /api/return-records/` requires `circulation.return_book`
- `POST /api/digital-books/` requires `digital.manage_digital_book`
- `PATCH /api/reviews/{id}/` requires `reviews.moderate_review`

Member-facing endpoints restrict records to the logged-in user's own data where appropriate.

## Input Validation

Serializers validate:

- User password handling
- Publication year range
- Shelf/location consistency
- Borrowing rules through circulation services
- Return validation through circulation services
- Renewal limits through circulation services
- Reservation rules through circulation services
- Fine payment/member matching
- Digital file extension and upload size
- Announcement publish/expiry dates
- Review ownership for ordinary members
- Feedback rating range through model validators

## Security Hardening

Settings now support environment variables through `.env`.

Security controls include:

- `DJANGO_SECRET_KEY` from environment
- `DJANGO_DEBUG` from environment
- `DJANGO_ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- secure cookie toggles
- HSTS toggles
- `SECURE_CONTENT_TYPE_NOSNIFF=True`
- `X_FRAME_OPTIONS="DENY"`
- upload size limits
- WhiteNoise static file handling
- PostgreSQL/MySQL-ready database configuration

## CSRF Protection

Django's `CsrfViewMiddleware` remains enabled for browser-based forms and session-authenticated DRF browsing.

JWT API clients authenticate with bearer tokens and do not rely on browser cookies. The browsable API still uses Django session authentication and CSRF protection.

## File Upload Security

Digital book uploads are restricted to:

- `.pdf`
- `.epub`
- `.mobi`
- `.azw3`
- `.txt`

Upload size is controlled by:

```text
MAX_UPLOAD_SIZE
```

Default: 10 MB.

## SQL Injection Protection

All data access uses Django ORM querysets, serializers, and parameterized database operations. Search and filter inputs are passed through ORM filters rather than raw SQL.

## XSS Protection

HTML templates use Django autoescaping by default. Security headers also include:

- `X_FRAME_OPTIONS="DENY"`
- `SECURE_CONTENT_TYPE_NOSNIFF=True`
- `SECURE_REFERRER_POLICY="same-origin"`

## Testing

Phase 8 adds tests for:

- JWT login and token refresh
- Role-based API permissions
- Borrowing through API service integration
- Digital file upload validation

Commands:

```bash
python3 manage.py test
python3 manage.py test apps.api
```

## Deployment Files

Added:

- `requirements.txt`
- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `gunicorn.conf.py`
- `deploy/nginx/library_management_system.conf`
- `docs/deployment_guide.md`

## Verification

Validated with:

```bash
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
python3 manage.py test apps.api
```

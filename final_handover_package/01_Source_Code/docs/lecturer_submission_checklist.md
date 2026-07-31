# Lecturer Submission Checklist

## Project Files

- Source code included.
- `README.md` included.
- `.env.example` included.
- `requirements.txt` included.
- Database migrations included.
- Documentation folder included.
- Docker deployment files included.
- Nginx and Gunicorn configuration included.

## Setup Verification

Run:

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py setup_admin --username admin --email admin@example.com --password Admin@12345
python3 manage.py seed_sample_data
python3 manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Demo Accounts

Main admin:

```text
username: admin
password: Admin@12345
```

Sample accounts:

```text
sample_admin / Password@123
sample_librarian / Password@123
sample_assistant / Password@123
sample_student / Password@123
sample_teacher / Password@123
sample_staff / Password@123
```

## Required Demo Flow

- Login as admin.
- Show dashboard statistics and charts.
- Show roles and permissions.
- Show members and profiles.
- Show book catalog, copies, shelves, and locations.
- Borrow a book.
- Return a book late and show fine calculation.
- Pay a fine.
- Reserve an unavailable book.
- Show due/overdue notifications.
- Record lost/damaged/repair status.
- Export reports.
- Upload digital book.
- Submit and moderate review.
- Publish announcement.
- Submit support ticket.
- Run API JWT login.
- Show Docker/deployment files.

## Final Test Commands

```bash
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
python3 manage.py test
DJANGO_DEBUG=False DJANGO_SECRET_KEY=production-grade-secret-key-with-more-than-fifty-characters-12345 DJANGO_ALLOWED_HOSTS=example.com CSRF_TRUSTED_ORIGINS=https://example.com CSRF_COOKIE_SECURE=True SESSION_COOKIE_SECURE=True SECURE_SSL_REDIRECT=True SECURE_HSTS_SECONDS=31536000 SECURE_HSTS_PRELOAD=True python3 manage.py check --deploy
```

## Submission Status

- Functional modules complete.
- Sample data complete.
- Automated tests complete.
- API complete.
- Deployment guide complete.
- Presentation outline complete.

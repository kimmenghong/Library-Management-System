# Administrator Manual

Project: Enterprise Library Management System  
Version: Corrected 11-table Django implementation

## 1. Administrator Role

The administrator is responsible for configuring the system, managing user access, protecting data, maintaining the database, and preparing the project for demonstration or deployment.

The active corrected system uses one Django application:

```text
apps.library
```

The application schema follows exactly 11 lecturer-required tables.

## 2. System Configuration

### 2.1 Environment File

System settings are controlled through `.env`.

Important settings:

| Setting | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secret key used by Django security features |
| `DJANGO_DEBUG` | Enables or disables debug mode |
| `DJANGO_ALLOWED_HOSTS` | Allowed hostnames |
| `DATABASE_ENGINE` | Database engine, usually `sqlite` for development |
| `SQLITE_NAME` | SQLite database file |
| `DEFAULT_FROM_EMAIL` | Default sender email |
| `EMAIL_BACKEND` | Email backend |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie setting |
| `SESSION_COOKIE_SECURE` | Secure session cookie setting |
| `SECURE_SSL_REDIRECT` | HTTPS redirect setting |

### 2.2 Development Configuration

Recommended development values:

```text
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,testserver
DATABASE_ENGINE=sqlite
SQLITE_NAME=library.sqlite3
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
```

### 2.3 Production Configuration

Recommended production values:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long-random-secret-key>
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

Use PostgreSQL or MySQL for production if required by the institution.

## 3. User And Role Management

### 3.1 Roles

Roles are stored in the `roles` table.

Recommended roles:

- Super Admin
- Admin
- Librarian
- Assistant Librarian
- Student
- Teacher
- Staff
- Guest

### 3.2 Users

Users are stored in the `users` table.

Each user has:

- Role
- Username
- Email
- Full name
- Phone
- Address
- Active status
- Staff status
- Superuser status

### 3.3 Creating A Superuser

Run:

```bash
python3 manage.py createsuperuser
```

Follow the prompts and enter:

- Username
- Email
- Full name
- Role
- Password

### 3.4 Managing Access

Access is controlled by:

- `is_active`
- `is_staff`
- `is_superuser`
- Role name

Library management pages are available to:

- Super Admin
- Admin
- Librarian
- Assistant Librarian
- Staff users marked as staff or superuser

### 3.5 Disabling A User

Instead of deleting a user:

1. Open the user record.
2. Uncheck Active.
3. Save.

This keeps historical records safe.

## 4. Backup And Restore

The corrected 11-table submission does not include a separate `backup_history` table because the lecturer required only 11 application tables. Backup and restore are handled administratively.

### 4.1 SQLite Backup

Stop the server, then copy the database file:

```bash
cp library.sqlite3 backups/library_backup.sqlite3
```

Recommended backup naming:

```text
library_backup_YYYY_MM_DD.sqlite3
```

### 4.2 SQLite Restore

Stop the server, then replace the database:

```bash
cp backups/library_backup.sqlite3 library.sqlite3
python3 manage.py migrate
```

### 4.3 Media Backup

Reports are stored under:

```text
media/reports/
```

Back up the `media/` folder if report files are required.

### 4.4 Full Project Backup

Back up:

- Source code
- `.env`
- `library.sqlite3`
- `media/`
- Documentation

Do not share `.env` publicly because it may contain secrets.

## 5. Database Maintenance

### 5.1 Apply Migrations

Run:

```bash
python3 manage.py migrate
```

### 5.2 Check Migration Drift

Run:

```bash
python3 manage.py makemigrations --check --dry-run
```

Expected result:

```text
No changes detected
```

### 5.3 Check Migrations

Run:

```bash
python3 manage.py showmigrations library
```

Expected result:

```text
library
 [X] 0001_initial
```

### 5.4 Load Sample Data

Run:

```bash
python3 manage.py seed_data
```

### 5.5 Database Integrity

For SQLite, verify integrity:

```bash
python3 manage.py shell
```

Then inspect using Django or SQLite tools if required.

The latest audit confirmed:

```text
FOREIGN_KEY_CHECK OK
INTEGRITY_CHECK ok
```

## 6. Security Management

### 6.1 Password Security

Django password hashing is used automatically. Administrators should:

- Use strong passwords.
- Avoid sharing admin accounts.
- Disable accounts that are no longer used.
- Change default sample passwords before any real deployment.

### 6.2 Secret Key

For production, change:

```text
DJANGO_SECRET_KEY
```

Use a long random value.

### 6.3 Debug Mode

Development:

```text
DJANGO_DEBUG=True
```

Production:

```text
DJANGO_DEBUG=False
```

Never deploy with debug mode enabled.

### 6.4 HTTPS Settings

For production:

```text
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

### 6.5 Access Review

Regularly review:

- Superuser accounts
- Staff accounts
- Role assignments
- Inactive accounts

### 6.6 File And Media Security

The current corrected system generates CSV report files. Administrators should:

- Keep media files private if they contain sensitive data.
- Avoid uploading unknown files.
- Back up generated reports if needed.

## 7. Administrator Routine Checklist

Daily:

- Check dashboard statistics.
- Review overdue books.
- Review unpaid fines.
- Review recent borrowing records.

Weekly:

- Back up the database.
- Check user accounts.
- Review book stock.
- Export important reports.

Before presentation:

- Run tests.
- Load sample data.
- Confirm sample accounts work.
- Confirm screenshots are ready.
- Confirm documentation is included.

## 8. Administrator Troubleshooting

### 8.1 Cannot Access Admin Panel

Check:

- User has `is_staff=True`.
- User has `is_superuser=True` if full admin access is required.
- Password is correct.

### 8.2 Migration Fails

Run:

```bash
python3 manage.py makemigrations --check --dry-run
python3 manage.py migrate
```

If errors continue, check model changes and migration files.

### 8.3 Static Files Missing

Run:

```bash
python3 manage.py collectstatic
```

### 8.4 Sample Accounts Missing

Run:

```bash
python3 manage.py seed_data
```

### 8.5 Permission Issue

Check:

- User role.
- `is_staff` flag.
- `is_active` flag.

# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| v1.0.0 | Yes |

## Reporting A Security Issue

For academic use, report security issues to the project maintainer or lecturer. Do not post sensitive security details publicly if they expose passwords, secret keys, database files, or private student data.

## Security Configuration

Before production deployment:

- Set `DJANGO_DEBUG=False`.
- Use a strong, private `DJANGO_SECRET_KEY`.
- Configure `DJANGO_ALLOWED_HOSTS`.
- Use HTTPS.
- Set `CSRF_COOKIE_SECURE=True`.
- Set `SESSION_COOKIE_SECURE=True`.
- Set `SECURE_SSL_REDIRECT=True`.
- Set `SECURE_HSTS_SECONDS=31536000` after confirming HTTPS is stable.
- Do not commit `.env`.
- Do not commit real production databases.
- Change sample passwords.

## Data Protection Notes

The system stores user, member, borrowing, fine, notification, and report data. Administrators should:

- Restrict staff access.
- Back up databases securely.
- Avoid sharing generated reports publicly.
- Disable inactive users.
- Use strong passwords.

## Known Security Limitations In v1.0.0

- The included `.env.example` is configured for development.
- The sample accounts use a public demo password.
- SQLite is intended for local development, not multi-user production deployment.
- Fine-grained permission tables are not active because the lecturer's schema requires only 11 application tables.

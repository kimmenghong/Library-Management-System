# DevOps and CI/CD Pipeline

Project: Enterprise Library Management System  
Backend: Django  
Database: Supabase PostgreSQL  
Authentication: Supabase Auth  
Frontend: Bootstrap 5  
Deployment: Render  
Business schema rule: keep the lecturer's required 11-table Data Dictionary unchanged.

This document defines the production-ready DevOps process for the project. It does
not add business features and does not modify the database schema.

---

## 1. Workflow Folder Structure

```text
.github/
└── workflows/
    ├── ci.yml
    ├── deploy-render.yml
    ├── database-maintenance.yml
    └── release.yml
```

| Workflow | Purpose | Trigger |
| --- | --- | --- |
| `ci.yml` | Code quality, security scan, Django checks, migrations check, tests, static build, production check | Push/PR to `main`, manual |
| `deploy-render.yml` | Triggers Render deployment after successful CI | Successful CI on `main`, manual |
| `database-maintenance.yml` | Manual Supabase backup and safe migration workflow | Manual only |
| `release.yml` | Creates or updates GitHub releases from semantic version tags | `v*.*.*` tag, manual |

---

## 2. GitHub Actions CI Pipeline

The CI pipeline contains three jobs.

### 2.1 Code Quality and Security

The `quality` job:

1. Checks out the repository.
2. Sets up Python 3.14.
3. Caches pip dependencies.
4. Installs development requirements.
5. Runs Black formatting check.
6. Runs isort import-order check.
7. Runs Flake8 linting.
8. Runs Bandit security scan.
9. Runs Safety dependency vulnerability scan.

Commands used:

```bash
black --check apps/library config manage.py
isort --check-only apps/library config manage.py
flake8 apps/library config manage.py
bandit -r apps/library config manage.py -x apps/library/migrations -s B105
safety check -r requirements.txt --full-report
```

`B105` is skipped because the project contains a guarded development-only
fallback secret in `settings.py`. Production rejects that key when `DEBUG=False`.

### 2.2 Django Checks, Migrations, and Tests

The `test` job:

1. Runs Django system checks.
2. Verifies that model changes have matching migrations.
3. Applies migrations to an isolated SQLite CI database.
4. Runs the complete Django test suite.
5. Runs `collectstatic` to verify static asset build.

Commands used:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py test
python manage.py collectstatic --noinput
```

The CI database uses SQLite so automated pull-request checks do not touch the
Supabase production database.

### 2.3 Production Configuration Verification

The `build` job:

1. Uses safe placeholder production environment values.
2. Runs Django deployment checks.
3. Builds static assets.
4. Verifies that the WSGI application imports successfully.

Commands used:

```bash
python manage.py check --deploy
python manage.py collectstatic --noinput
python -c "import config.wsgi; print('WSGI import OK')"
```

---

## 3. Code Quality Tools

| Tool | Purpose |
| --- | --- |
| Black | Enforces Python code formatting. |
| isort | Enforces import ordering. |
| Flake8 | Detects style and code-quality issues. |
| Bandit | Scans Python code for security risks. |
| Safety | Scans Python dependencies for known vulnerabilities. |

Install locally:

```bash
pip install -r requirements-dev.txt
```

Run locally:

```bash
black --check apps/library config manage.py
isort --check-only apps/library config manage.py
flake8 apps/library config manage.py
bandit -r apps/library config manage.py -x apps/library/migrations -s B105
safety check -r requirements.txt --full-report
```

---

## 4. Continuous Deployment to Render

The `deploy-render.yml` workflow triggers Render deployment only after CI passes
on the `main` branch.

Recommended Render setup:

| Setting | Value |
| --- | --- |
| Service Type | Web Service |
| Runtime | Python |
| Branch | `main` |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --access-logfile - --error-logfile -` |
| Health Check Path | `/` |
| Auto Deploy | Enabled or controlled by deploy hook |

### Deployment Flow

1. Developer opens a pull request.
2. GitHub Actions runs CI.
3. Code is reviewed and merged into `main`.
4. CI runs again on `main`.
5. If CI succeeds, GitHub Actions triggers the Render deploy hook.
6. Render builds the app using `build.sh`.
7. Render starts Gunicorn.
8. Developer verifies the deployed website.

### Rollback Strategy

Use one of these safe rollback methods:

1. Render Dashboard: redeploy the previous successful deployment.
2. Git: revert the bad commit and push to `main`.
3. GitHub Release: check out a previous tag and redeploy.
4. Database: restore from the latest Supabase backup only when data corruption occurred.

---

## 5. Required GitHub Secrets

Use secret names only. Never commit real values.

### Render Deployment

```text
RENDER_DEPLOY_HOOK_URL
```

Optional for future Render API automation:

```text
RENDER_API_KEY
RENDER_SERVICE_ID
```

### Supabase Database Maintenance

```text
SECRET_KEY
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
DATABASE_HOST
DATABASE_PORT
SUPABASE_DATABASE_URL
```

`SUPABASE_DATABASE_URL` should use a secure PostgreSQL URL with SSL enabled.
Do not print it in logs.

### Supabase Auth for Render Environment

These are configured in Render, not required for normal CI:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
USE_SUPABASE_AUTH
```

Do not store the Supabase service-role key unless a future admin-only workflow
requires it. The current application does not need it.

---

## 6. Database Pipeline

Production database migrations should be deliberate because the application uses
Supabase PostgreSQL.

### 6.1 Migration Verification

CI always runs:

```bash
python manage.py makemigrations --check --dry-run
```

This confirms that model changes and migration files are synchronized.

### 6.2 Backup Before Migrations

Use the manual `database-maintenance.yml` workflow with action
`backup-and-migrate`.

The workflow:

1. Installs PostgreSQL client tools.
2. Verifies database secrets are present.
3. Runs `pg_dump` against Supabase.
4. Uploads the backup as a GitHub Actions artifact.
5. Verifies migration files.
6. Runs `python manage.py migrate --noinput`.

### 6.3 Manual Backup Command

For local administrator use:

```bash
pg_dump "$SUPABASE_DATABASE_URL" \
  --format=custom \
  --no-owner \
  --no-acl \
  --file "library_backup_YYYYMMDD_HHMMSS.dump"
```

### 6.4 Restore Procedure

Use restore only when necessary and only after confirming the target database.

```bash
pg_restore "$BACKUP_FILE" \
  --dbname "$SUPABASE_DATABASE_URL" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl
```

Before restore:

1. Confirm the backup file is valid.
2. Confirm the target Supabase project.
3. Stop writes to the application if possible.
4. Download a fresh backup before restoring.
5. Verify the 11 business tables after restore.

### 6.5 Schema Rule

Migrations must preserve these required business tables:

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

Do not introduce extra business tables unless the lecturer changes the Data
Dictionary requirement.

---

## 7. Monitoring and Notifications

### Build Monitoring

Check:

- GitHub Actions CI status.
- Failed step logs.
- Safety and Bandit scan output.
- Migration-check output.
- Test summary.

### Deployment Monitoring

Check:

- Render build logs.
- Render deploy status.
- Gunicorn startup logs.
- Application health check at `/`.
- Django error logs.
- Supabase connection usage.

### Failed Build Handling

1. Open the failed GitHub Actions job.
2. Identify whether failure is formatting, lint, security, migration, or test.
3. Reproduce locally.
4. Fix in a branch.
5. Push and wait for CI to pass.
6. Merge only after green CI.

### Failed Deployment Handling

1. Open Render logs.
2. Check environment variables.
3. Check dependency installation.
4. Check `collectstatic`.
5. Check database connection.
6. Check Gunicorn WSGI startup.
7. Redeploy previous successful deployment if needed.

Notification options:

- GitHub email notifications.
- Render dashboard notifications.
- GitHub branch protection status checks.
- Optional Slack/Teams webhook in future.

---

## 8. Release Management

Use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Examples:

| Version | Meaning |
| --- | --- |
| `v1.0.0` | First stable final submission release. |
| `v1.0.1` | Bug fix only. |
| `v1.1.0` | New backward-compatible feature. |
| `v2.0.0` | Major breaking change. |

### Release Steps

```bash
git checkout main
git pull origin main
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

Pushing a tag matching `v*.*.*` runs `release.yml` and creates or updates the
GitHub release.

### Changelog

Update `CHANGELOG.md` before creating a release:

```text
## v1.0.0
- Corrected 11-table Data Dictionary.
- Added Supabase PostgreSQL configuration.
- Added Supabase Auth integration.
- Added borrowing, returning, fines, notifications, reports, and tests.
```

---

## 9. Disaster Recovery

### Application Recovery

Use this order:

1. Redeploy previous Render deployment.
2. Revert the latest Git commit.
3. Deploy from a known-good release tag.
4. Restore environment variables from `.env.example` names and secure password manager values.

### Database Recovery

Use this order:

1. Stop or pause risky write operations.
2. Create a fresh backup of the current state.
3. Identify the latest valid backup.
4. Restore using `pg_restore`.
5. Run `python manage.py migrate --noinput`.
6. Verify the 11 required tables.
7. Test login, dashboard, borrowing, returning, fines, notifications, and reports.

### Secret Exposure Recovery

If any secret is exposed:

1. Remove the exposed value from Git immediately.
2. Rotate the Django secret key if needed.
3. Rotate Supabase database password.
4. Rotate Supabase keys if required.
5. Update Render environment variables.
6. Redeploy the app.
7. Review Git history and GitHub Actions logs.

---

## 10. Deployment Verification Checklist

Before merging:

- [ ] `black --check` passes.
- [ ] `isort --check-only` passes.
- [ ] `flake8` passes.
- [ ] `bandit` passes.
- [ ] `safety` scan reviewed.
- [ ] `python manage.py check` passes.
- [ ] `python manage.py makemigrations --check --dry-run` passes.
- [ ] `python manage.py test` passes.
- [ ] `collectstatic` passes.

After deployment:

- [ ] Render build succeeds.
- [ ] Gunicorn starts successfully.
- [ ] Homepage loads.
- [ ] Login page loads with library image.
- [ ] Supabase Auth login works.
- [ ] Dashboard loads.
- [ ] Books page loads.
- [ ] Members page loads.
- [ ] Borrowing works.
- [ ] Returning works.
- [ ] Fine calculation works.
- [ ] Notifications load.
- [ ] Reports load.
- [ ] Static files load.
- [ ] Supabase tables remain the required 11 business tables.

---

## 11. Maintenance Recommendations

Daily:

- Check Render service status.
- Check application logs for errors.
- Check Supabase connection health.

Weekly:

- Run dependency update review.
- Run test suite locally.
- Download or verify database backup.
- Review failed login patterns.

Monthly:

- Review GitHub secrets.
- Rotate demo passwords if needed.
- Review Supabase Auth users.
- Review database size and performance.
- Create a tagged release after stable changes.

Before lecturer demonstration:

- Confirm Render URL works.
- Confirm Supabase Auth works.
- Confirm sample data exists.
- Confirm screenshots are ready.
- Confirm no secrets are visible.
- Run final tests.

---

## 12. Final Notes

The CI/CD pipeline is intentionally conservative:

- Pull-request CI uses SQLite and does not touch Supabase production.
- Production database migration is manual and can create a backup first.
- Deployment runs only after CI succeeds.
- Secrets are stored in GitHub/Render settings, never in source code.
- The lecturer's required 11-table Data Dictionary remains unchanged.


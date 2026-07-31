# Post-Deployment Maintenance and Recovery Guide

## Monitoring

- Check Render service uptime daily.
- Review Render logs after each deployment.
- Review Django warnings and errors.
- Monitor Supabase database connections and storage usage.
- Watch failed Supabase Auth login attempts.
- Test slow pages such as dashboard, books, reports, and borrowing records.

## Backup Plan

Database backup:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
pg_dump "$DATABASE_URL" --format=custom --file library_backup_YYYY_MM_DD.dump
```

Restore to a test database first:

```bash
pg_restore --dbname="$DATABASE_URL" --clean --if-exists library_backup_YYYY_MM_DD.dump
```

Application backup:

- Push source code to GitHub.
- Keep `.env.example`.
- Never commit `.env`.
- Back up screenshots, reports, manuals, and presentation files.
- Create versioned releases.

## Security Maintenance

- Keep `DEBUG=False` in production.
- Rotate exposed keys immediately.
- Disable inactive users.
- Review Supabase Auth users.
- Review role-based permissions.
- Run `python manage.py check --deploy`.
- Scan GitHub before submission for secrets.

## Update Procedure

```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
git add .
git commit -m "Maintenance update"
git push origin main
```

After Render redeploys:

```bash
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
```

## Emergency Recovery

Website offline:

- Check Render status and service logs.
- Restart the Render service.
- Redeploy the last successful commit.

Build fails:

- Check `requirements.txt`, `runtime.txt`, and `build.sh`.
- Run the build commands locally.

Supabase unavailable:

- Check Supabase service status.
- Confirm database host, user, password, and SSL mode.
- Switch to Supabase Session Pooler if direct connection fails.

Login fails:

- Confirm `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
- Confirm the local Django `users` table has a matching active user with a role.

Data deleted:

- Stop write operations if possible.
- Restore from the latest verified backup.
- Test restore before applying to production.

# Deployment Guide

## 1. Prepare Environment

Create a production `.env` file:

```bash
cp .env.example .env
```

Set at least:

```text
DJANGO_SECRET_KEY=<strong-random-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_PRELOAD=True
```

## 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Database Migration Guide

Development SQLite:

```bash
python3 manage.py migrate
```

PostgreSQL production:

```text
DATABASE_ENGINE=postgresql
DATABASE_NAME=library_management
DATABASE_USER=library_user
DATABASE_PASSWORD=<secure-password>
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
```

Then run:

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

To move from SQLite to PostgreSQL:

```bash
python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
```

Switch `.env` to PostgreSQL, migrate, then load:

```bash
python3 manage.py migrate
python3 manage.py loaddata data.json
```

## 4. Static Files

```bash
python3 manage.py collectstatic --noinput
```

## 5. Gunicorn

Run locally:

```bash
gunicorn config.wsgi:application --config gunicorn.conf.py
```

Systemd example:

```ini
[Unit]
Description=Library Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/library-management-system
EnvironmentFile=/var/www/library-management-system/.env
ExecStart=/var/www/library-management-system/.venv/bin/gunicorn config.wsgi:application --config gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 6. Nginx

Use:

```text
deploy/nginx/library_management_system.conf
```

Update:

```text
server_name example.com;
```

Then link and reload:

```bash
sudo ln -s /var/www/library-management-system/deploy/nginx/library_management_system.conf /etc/nginx/sites-enabled/library_management_system
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Docker Deployment

```bash
docker compose up --build
```

Create superuser inside the container:

```bash
docker compose exec web python manage.py createsuperuser
```

## 8. Production Checklist

- `DJANGO_DEBUG=False`
- strong `DJANGO_SECRET_KEY`
- correct `DJANGO_ALLOWED_HOSTS`
- HTTPS configured
- secure cookies enabled
- HSTS enabled after HTTPS is stable
- PostgreSQL database backed up
- media directory backed up
- `python3 manage.py check --deploy` reviewed
- admin password stored securely
- API JWT tested
- Nginx upload limit matches `MAX_UPLOAD_SIZE`

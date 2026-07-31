# Submission README

## Project Information

- Project name: Enterprise Library Management System
- Version: 1.0.0
- Backend: Django
- Database: Supabase PostgreSQL
- Authentication: Supabase Auth
- Frontend: Bootstrap 5
- Hosting: Render
- Required database: 11-table lecturer Data Dictionary

## How to Run Locally

```bash
cd "01_Source_Code"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Required Environment Variables

Use `.env.example` as the template. Never commit real values.

Required production values:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_ENGINE=postgresql`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `DATABASE_SSLMODE=require`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## Verification Commands

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
python manage.py check --deploy
```

## Important Security Notes

- `.env` is excluded from submission.
- Supabase service-role key is not required for normal deployment.
- Real production passwords are not included.
- Demo passwords are for demonstration only.

## Lecturer Review Path

1. Read the final report in `03_Final_Report`.
2. Review the data dictionary in `02_Database`.
3. Install and run the source code from `01_Source_Code`.
4. Review testing documentation in `05_Testing_Documentation`.
5. Use presentation files in `06_Presentation`.
6. Use screenshots and video from `07_Screenshots` and `08_Demo_Video`.

# Contributing

Thank you for your interest in improving the Library Management System.

This project is a university final project release. The v1.0.0 version is intentionally aligned with the lecturer's required 11-table Data Dictionary. Contributions should preserve that schema unless a future version explicitly changes the project scope.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py seed_data
python3 manage.py runserver
```

## Before Submitting Changes

Run:

```bash
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
python3 manage.py test
```

Expected result:

```text
System check identified no issues.
No changes detected.
Tests pass.
```

## Contribution Rules

- Keep code readable and consistent with existing Django patterns.
- Do not add new application tables to the corrected v1.0.0 schema unless the project scope changes.
- Preserve the required 11 table names and primary key names.
- Add tests for new behavior.
- Update documentation when behavior changes.
- Do not commit `.env`, virtual environments, cache folders, or local database files.

## Commit Message Style

Use short, clear commit messages:

```text
docs: update user manual
fix: correct fine payment validation
test: add borrow workflow coverage
```

## Pull Request Checklist

- [ ] Code is tested.
- [ ] Migrations are intentional.
- [ ] Documentation is updated.
- [ ] The 11-table Data Dictionary remains valid.
- [ ] No secrets or local files are committed.

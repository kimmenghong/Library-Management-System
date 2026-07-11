# Code Phase 8: Dashboard and Operational Analytics

## Scope

This phase completes the `dashboard` Django app. It provides permission-protected library statistics, operational alerts, circulation rankings, inventory and borrowing charts, role-targeted announcements, recent activity, responsive Bootstrap presentation, and a read-only REST endpoint.

## App Structure

```text
apps/dashboard/
├── __init__.py
├── admin.py
├── api.py
├── apps.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py

templates/dashboard/
└── dashboard.html

static/dashboard/js/
└── dashboard.js
```

The dashboard is a read-only projection over existing application data. It deliberately owns no database tables, forms, or admin registrations, so no dashboard migration is required.

## Statistics

- Total catalog titles and physical copies
- Total and active members
- Available and borrowed copies
- Active, due-today, and overdue loans
- Pending and ready reservations
- Lost, damaged, and under-repair copies
- Outstanding fine count and remaining balance
- Physical inventory utilization percentage

## Analytics

- Six-month borrowing trend with zero-filled missing months
- Copy status distribution for every supported status
- Top eight categories by title count
- Five most borrowed books with total and active loan counts
- Five members with the highest number of active loans

The service layer uses database aggregation and optimized related-object loading. Dashboard GET requests do not update circulation records; overdue totals are calculated from active loan status and due date.

## Permissions and Privacy

- Page access requires `dashboard.view_dashboard`.
- Quick actions are shown only when the user has the corresponding catalog, circulation, or report permission.
- Recent borrowing is loaded only with `circulation.view_borrow`.
- Recent activity is loaded only with `activity.view_activity`.
- Announcements must be published, current, and either global or targeted to the signed-in user's role.
- Superusers retain the project's standard permission bypass.

## Main URLs

```text
/dashboard/       Operational dashboard
/api/dashboard/   Read-only dashboard metrics and chart data
```

The API endpoint requires authentication and `dashboard.view_dashboard`. Its response contains `generated_at`, `metrics`, and `charts`; no serializer is needed because the payload is computed data rather than a model resource.

## Frontend

- Bootstrap 5 responsive layout
- Compact metric cards and operational alert bands
- Chart.js line, doughnut, and horizontal bar charts
- Lucide quick-action icons
- Accessible canvas labels and text values
- Graceful message when the chart library is unavailable
- Stable chart dimensions and mobile layouts

The base template now exposes `extra_css` and `extra_js` blocks so page-specific assets can load after shared assets without duplicating the document shell.

## Verification

```bash
python manage.py collectstatic --noinput
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.dashboard
python manage.py test
```

This phase adds 13 focused tests for analytics, date boundaries, fine totals, announcement targeting, page permissions, sensitive recent data, quick-action visibility, and REST API access.

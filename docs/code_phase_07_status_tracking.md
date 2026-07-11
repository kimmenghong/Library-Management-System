# Code Phase 7: Book Status Tracking, Lost, Damaged, and Repair Records

## Scope

This phase completes the `status_tracking` Django app for physical book-copy lifecycle tracking. It covers immutable status logs, lost-book records, damaged-book records, repair records, automatic copy/book status synchronization, member notifications, cost-based fine creation, Django Admin integration, Bootstrap templates, REST API integration, and regression tests.

## App Structure

```text
apps/status_tracking/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_damagedbook_resolved_date_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py

templates/status_tracking/
├── damagedbook_detail.html
├── damagedbook_form.html
├── damagedbook_list.html
├── lostbook_detail.html
├── lostbook_form.html
├── lostbook_list.html
├── repair_detail.html
├── repair_form.html
├── repair_list.html
├── status_log_list.html
└── status_tabs.html
```

REST serializers and viewsets are integrated in `apps/api/serializers.py` and `apps/api/views.py`.

## Models

- `BookStatusLog`: immutable audit-style copy status history with previous status, new status, reason, notes, user, book, and copy.
- `LostBook`: lost-copy workflow with member, borrow record, replacement cost, reported/resolved dates, and statuses such as reported, charged, paid, recovered, replaced, and written off.
- `DamagedBook`: damage workflow with severity, repair cost estimate, member, borrow record, resolution notes, and statuses such as reported, under review, sent to repair, repaired, and written off.
- `RepairRecord`: repair workflow with vendor, sent date, expected return date, completed date, cost, notes, and under repair/completed/cancelled statuses.

## Business Rules

- Every copy status change creates a `BookStatusLog` row.
- Duplicate open lost, damaged, or repair records for the same copy are blocked.
- Lost, damaged, and repair costs cannot be negative.
- Resolved lost/damaged records must have a resolved date.
- Completed repairs must have a completed date.
- Repair records must reference a damage record for the same copy when one is selected.
- Lost or damaged reports tied to an active loan close that loan as lost or damaged.
- Reporting a lost copy sets the copy to `lost` and synchronizes the parent book status.
- Reporting a damaged copy sets the copy to `damaged`, marks its condition damaged, and synchronizes the parent book status.
- Sending a copy to repair sets the copy to `under_repair`.
- Completing a repair sets the damage record to repaired and returns the copy to available/good condition.
- Recovering or replacing a lost copy returns the copy to available/good condition.
- Replacement and repair costs create member fines when a member is attached.
- Lost and damaged reports notify the affected member through the notification service.
- Admin, template views, and REST API all call the same service functions so behavior stays consistent.

## Main URLs

```text
/status/                         Book status log list
/status/lost/                    Lost-book records
/status/lost/create/             Report a lost book
/status/lost/<id>/               Lost-book detail
/status/lost/<id>/edit/          Update lost-book status
/status/damaged/                 Damaged-book records
/status/damaged/create/          Report damaged book
/status/damaged/<id>/            Damaged-book detail
/status/damaged/<id>/edit/       Update damaged-book status
/status/repairs/                 Repair records
/status/repairs/create/          Send copy to repair
/status/repairs/<id>/            Repair detail
/status/repairs/<id>/edit/       Update repair status
```

## REST Operations

```text
GET       /api/book-status-logs/
GET       /api/book-status-logs/<id>/
GET, POST /api/lost-books/
GET, PUT, PATCH, DELETE /api/lost-books/<id>/
GET, POST /api/damaged-books/
GET, PUT, PATCH, DELETE /api/damaged-books/<id>/
GET, POST /api/repair-records/
GET, PUT, PATCH, DELETE /api/repair-records/<id>/
```

## Verification

```bash
python manage.py check
python manage.py migrate status_tracking
python manage.py test apps.status_tracking
python manage.py test
```

This phase adds 15 focused tests. The complete project suite contains 139 passing tests after this phase.

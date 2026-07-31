# Code Phase 4: Circulation and Reservations

## Scope

This phase completes the `circulation` Django app for borrowing, returning, renewals, reservation queues, borrowing policies, automatic late-fine calculation, physical-copy status synchronization, role-scoped history, and REST API integration.

Fine balances and payments remain owned by the separate `fines` app; circulation creates a late-return fine when a returned loan is overdue.

## App Structure

```text
apps/circulation/
├── migrations/
│   ├── 0001_initial.py
│   ├── 0002_seed_borrowing_policies.py
│   └── 0003_alter_reservation_options_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py

templates/circulation/
├── borrow_detail.html
├── borrow_form.html
├── borrow_list.html
├── circulation_tabs.html
├── policy_form.html
├── policy_list.html
├── renew_form.html
├── renewal_list.html
├── reservation_form.html
├── reservation_list.html
├── reservation_status_form.html
├── return_form.html
└── return_list.html
```

REST serializers and viewsets are integrated in `apps/api/serializers.py` and `apps/api/views.py`.

## Models

- `BorrowingPolicy`: member-type limits, loan and renewal periods, fine rate, pickup window, and service availability
- `BorrowRecord`: immutable issue history, due date, current state, renewal count, and historical fine-rate snapshot
- `ReturnRecord`: one validated return transaction per loan, including condition and calculated late fine
- `RenewalRecord`: append-only due-date extension history
- `Reservation`: FIFO title-level queue with pending, ready, fulfilled, cancelled, and expired states

## Business Rules

- Only active, unexpired members with active roles may borrow, renew, or reserve.
- Members with unpaid fines cannot borrow, renew, or reserve.
- Borrow limits, loan periods, renewal limits, renewal periods, and pickup windows are member-type policies.
- A physical copy can have only one active loan, protected by service locking and a partial database constraint.
- A member cannot borrow a second copy of the same title.
- Due dates cannot exceed policy limits through standard UI or API workflows.
- Each loan snapshots its fine rate, so later policy changes do not rewrite historical charges.
- Returns reject future dates, duplicate returns, inactive loans, and dates before the issue date.
- Returning a good copy makes it available; lost, damaged, and repair returns update copy and title status and create status-tracking records.
- Late returns create an unpaid fine using `days_late × captured_fine_rate_per_day`.
- Renewals are blocked for overdue loans, unpaid fines, inactive policies, exhausted limits, and another member's active reservation.
- Reservations require registered stock with no currently available copy.
- Members cannot reserve a title they already hold or create duplicate active reservations.
- Pending reservations have no artificial expiry date. A pickup expiry is assigned only when a copy becomes available.
- One ready reservation is allowed per title, and the oldest pending reservation is promoted first.
- Returning or restoring an available copy promotes the next reservation and creates an in-app notification.
- Members can view only their own loans, returns, renewals, and reservations. Library operators can view all records.
- Transaction rows are read-only in Django Admin and cannot be patched or deleted through the REST API; changes must use atomic service workflows.

## Main URLs

```text
/circulation/                         Loan history and search
/circulation/borrow/                  Issue an available copy
/circulation/borrows/<id>/            Loan details
/circulation/borrows/<id>/return/     Process a return
/circulation/borrows/<id>/renew/      Renew an active loan
/circulation/returns/                 Return history
/circulation/renewals/                Renewal history
/circulation/reservations/            Reservation queue and history
/circulation/reservations/create/     Create a reservation
/circulation/reservations/<id>/edit/  Transition or cancel a reservation
/circulation/policies/                Borrowing policy administration
```

## REST Operations

```text
GET, POST /api/borrow-records/
GET, POST /api/return-records/
GET, POST /api/renewal-records/
GET, POST /api/reservations/
POST      /api/reservations/<id>/status/
GET       /api/borrowing-policies/
```

Write access is checked against the custom role-permission system. Member-facing querysets are restricted to the authenticated member account.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test apps.circulation
python manage.py test
```

The circulation suite contains 28 focused tests. The complete project suite contains 85 passing tests after this phase.

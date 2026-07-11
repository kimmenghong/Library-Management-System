# Code Phase 5: Fine Management and Payment History

## Scope

This phase completes the `fines` Django app for manual and circulation-generated fines, outstanding balances, partial and full payments, audited waivers, payment reversals, member privacy, Django Admin visibility, and REST API integration.

## App Structure

```text
apps/fines/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_fine_updated_by_fine_waived_at_fine_waived_by_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py

templates/fines/
├── fine_detail.html
├── fine_form.html
├── fine_list.html
├── fine_tabs.html
├── fine_waive_form.html
├── payment_detail.html
├── payment_form.html
├── payment_list.html
└── payment_void_form.html
```

REST serializers and viewsets are integrated in `apps/api/serializers.py` and `apps/api/views.py`.

## Models

- `Fine`: member charge, optional loan relationship, assessed amount, cached paid total, balance status, creation/update actors, and waiver audit data
- `Payment`: immutable payment history with method, date, reference, receiving operator, completion state, and void audit data

## Business Rules

- Fine amounts and payment amounts must be greater than zero.
- A fine linked to a loan must belong to the same member as that loan.
- Late-return fines require a loan relationship, and each loan can have only one late-return fine.
- Paid totals must remain between zero and the assessed fine amount.
- Fine status is derived from completed payment history: unpaid, partially paid, or paid.
- The outstanding balance is `amount - paid_amount`; waived fines have a zero collectible balance.
- Fine amount, member, loan, and reason cannot change after payment history exists.
- Waivers require an outstanding fine, an operator, a timestamp, and a reason.
- A waived fine cannot be reopened or receive additional payments.
- Payments are recorded inside a transaction that locks the fine before validating its current balance.
- Concurrent or stale requests cannot overpay a fine.
- Payment ownership is always derived from the fine and cannot be supplied independently.
- Payment dates cannot be in the future.
- Completed payment details are immutable and payment rows cannot be deleted.
- Corrections use an audited void workflow; voiding recalculates the fine while preserving history.
- Student, teacher, and staff accounts can view only their own fines and payments.
- Librarians and administrators use explicit role permissions to assess, collect, waive, or void.
- Django Admin exposes financial rows as read-only history. Custom UI and API services own all state transitions.
- REST resources reject update, patch, and delete operations for financial transactions.

## Data Migration

Migration `0002` safely upgrades existing data before constraints are added:

- Recalculates paid totals from payment rows
- Repairs member ownership from the related fine and loan
- Preserves legacy waivers with migration audit text
- Normalizes invalid or future payment data
- Consolidates duplicate late-return fines without dropping payment rows
- Grants members permission to view their own payment history

## Main URLs

```text
/fines/                         Fine list, balances, search, and filters
/fines/create/                  Assess a manual fine
/fines/<id>/                    Fine details and payment history
/fines/<id>/edit/               Edit an unpaid fine without payments
/fines/<id>/waive/              Waive an outstanding balance
/fines/<id>/payments/create/    Record payment for a selected fine
/fines/payments/                Payment history
/fines/payments/create/         Record a payment
/fines/payments/<id>/           Payment details
/fines/payments/<id>/void/      Void and reverse a payment
```

## REST Operations

```text
GET, POST /api/fines/
GET       /api/fines/<id>/
POST      /api/fines/<id>/waive/
GET, POST /api/payments/
GET       /api/payments/<id>/
POST      /api/payments/<id>/void/
```

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test apps.fines
python manage.py test
```

The fine and payment suite contains 19 focused tests. The complete project suite contains 104 passing tests after this phase.

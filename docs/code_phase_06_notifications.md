# Code Phase 6: Notifications and Email Reminders

## Scope

This phase completes the `notifications` Django app for personal in-app messages, due-date and overdue reminders, email delivery attempts, failed-delivery retries, member notification history, scheduled execution, role-based privacy, and REST API integration.

Lost, damaged, and repair records remain owned by the separate `status_tracking` app; those workflows call this app's notification service.

## App Structure

```text
apps/notifications/
├── management/commands/
│   └── send_library_reminders.py
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_alter_emailreminder_options_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py

templates/notifications/
├── email_reminder_detail.html
├── email_reminder_list.html
├── member_notification_history.html
├── notification_detail.html
├── notification_form.html
├── notification_list.html
├── notification_tabs.html
└── reminder_run.html
```

REST serializers and viewsets are integrated in `apps/api/serializers.py` and `apps/api/views.py`.

## Models

- `Notification`: recipient, message type, channel, priority, read/archive state, related loan/copy, daily deduplication key, and email delivery summary
- `EmailReminder`: append-only email attempt with recipient snapshot, attempt number, pending/sent/failed state, timestamps, and failure details

## Business Rules

- Members can view, read, and archive only their own notifications.
- Library operators can view all member histories and create manual notifications.
- A notification related to a loan must use that loan's member and physical copy.
- Read and archived states carry coherent audit timestamps enforced by model and database constraints.
- Email delivery state and delivery timestamp must always agree.
- Choosing the email or combined channel automatically creates an email attempt.
- Each email begins as pending, then becomes sent or failed; delivery rows are append-only and cannot be deleted.
- Failed attempts preserve the backend error and can be retried as a new numbered attempt.
- A recent pending attempt prevents two workers from sending the same email concurrently.
- Pending attempts older than `EMAIL_PENDING_TIMEOUT_MINUTES` are failed automatically before retry.
- Successful delivery updates the parent notification once and suppresses further sends.
- Missing member email addresses produce a failed attempt without using a fake address.
- Due-date and overdue reminders use a unique loan/type/date key, making repeated daily jobs idempotent.
- Overdue generation first synchronizes active loan status.
- Email logs and REST querysets use the same member privacy rules as the in-app inbox.
- Django Admin exposes notifications and delivery attempts as read-only operational history.

## Main URLs

```text
/notifications/                         Personal or operator notification list
/notifications/create/                  Create a manual notification
/notifications/run-reminders/           Run due-date and overdue reminders
/notifications/mark-all-read/           Mark the visible inbox as read
/notifications/<id>/                    Notification details
/notifications/<id>/read/               Mark one notification read
/notifications/<id>/archive/            Archive one notification
/notifications/members/<member-id>/     Member notification history
/notifications/email-reminders/         Email delivery attempts
/notifications/email-reminders/<id>/    Delivery attempt details
/notifications/email-reminders/<id>/retry/  Retry failed delivery
```

## Scheduled Reminders

Run the command manually or schedule it with cron, systemd, or the deployment platform:

```bash
python manage.py send_library_reminders --days 3
```

Useful options:

```bash
python manage.py send_library_reminders --days 3 --no-email
python manage.py send_library_reminders --due-only
python manage.py send_library_reminders --overdue-only
```

The command is safe to repeat on the same day because reminder keys are unique.

## REST Operations

```text
GET, POST /api/notifications/
GET       /api/notifications/<id>/
POST      /api/notifications/<id>/read/
POST      /api/notifications/<id>/archive/
POST      /api/notifications/<id>/retry-email/
GET       /api/email-reminders/
GET       /api/email-reminders/<id>/
```

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test apps.notifications
python manage.py test
```

The notification suite contains 20 focused tests. The complete project suite contains 124 passing tests after this phase.

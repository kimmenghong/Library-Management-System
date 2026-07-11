# Final Submission Package

Project title: Library Management System

This document prepares the corrected Library Management System for university final project submission. It focuses only on the lecturer's required 11 application tables and the active Django implementation in `apps.library`.

## 1. Final Project Folder Structure

```text
Library Management System/
|-- apps/
|   |-- library/
|   |   |-- management/
|   |   |   `-- commands/
|   |   |       `-- seed_data.py
|   |   |-- migrations/
|   |   |   |-- 0001_initial.py
|   |   |   `-- __init__.py
|   |   |-- __init__.py
|   |   |-- admin.py
|   |   |-- apps.py
|   |   |-- forms.py
|   |   |-- models.py
|   |   |-- test_runner.py
|   |   |-- tests.py
|   |   |-- urls.py
|   |   `-- views.py
|   `-- __init__.py
|-- config/
|   |-- __init__.py
|   |-- asgi.py
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- docs/
|   `-- final_submission_package_11_table.md
|-- media/
|   `-- reports/
|-- static/
|   |-- css/
|   |   `-- style.css
|   `-- js/
|       `-- main.js
|-- templates/
|   `-- library/
|       |-- base.html
|       |-- book_list.html
|       |-- borrow_form.html
|       |-- borrow_list.html
|       |-- confirm_delete.html
|       |-- dashboard.html
|       |-- entity_form.html
|       |-- entity_list.html
|       |-- fine_list.html
|       |-- fine_payment_form.html
|       |-- login.html
|       |-- notification_list.html
|       |-- report_list.html
|       `-- return_form.html
|-- .env.example
|-- library.sqlite3
|-- manage.py
|-- requirements.txt
`-- README.md
```

Submission note: the workspace may still contain older phase-development folders from earlier iterations. The corrected final project is the active `apps.library` implementation. In `config/settings.py`, only `apps.library.apps.LibraryConfig` is installed as the Library Management System application.

## 2. Final Database Schema Summary

The lecturer's application Data Dictionary contains exactly 11 required tables.

| No. | Table | Primary Key | Purpose |
| --- | --- | --- | --- |
| 1 | `roles` | `role_id` | Stores user role names and descriptions |
| 2 | `users` | `user_id` | Stores login accounts and user details |
| 3 | `categories` | `category_id` | Stores book categories |
| 4 | `authors` | `author_id` | Stores book authors |
| 5 | `publishers` | `publisher_id` | Stores book publishers |
| 6 | `books` | `book_id` | Stores book catalog and stock information |
| 7 | `members` | `member_id` | Stores library member information |
| 8 | `borrow_records` | `borrow_id` | Stores borrowing and return transactions |
| 9 | `fines` | `fine_id` | Stores late return fine records |
| 10 | `notifications` | `notification_id` | Stores member notification history |
| 11 | `reports` | `report_id` | Stores generated report history |

Django support tables may also exist in the development database because Django Admin, authentication, sessions, content types, and migrations need them. They are not Library Management System Data Dictionary tables.

## 3. Data Dictionary Verification Checklist

| Requirement | Status |
| --- | --- |
| `roles` table exists with PK `role_id` | Completed |
| `users` table exists with PK `user_id` | Completed |
| `users.role_id` connects to `roles.role_id` | Completed |
| `categories` table exists with PK `category_id` | Completed |
| `authors` table exists with PK `author_id` | Completed |
| `publishers` table exists with PK `publisher_id` | Completed |
| `books` table exists with PK `book_id` | Completed |
| `books.category_id` connects to `categories.category_id` | Completed |
| `books.author_id` connects to `authors.author_id` | Completed |
| `books.publisher_id` connects to `publishers.publisher_id` | Completed |
| `members` table exists with PK `member_id` | Completed |
| `members.user_id` connects to `users.user_id` | Completed |
| `borrow_records` table exists with PK `borrow_id` | Completed |
| `borrow_records.member_id` connects to `members.member_id` | Completed |
| `borrow_records.book_id` connects directly to `books.book_id` | Completed |
| `borrow_records.issued_by` connects to `users.user_id` | Completed |
| `borrow_records.received_by` connects to `users.user_id` | Completed |
| Borrow records do not use `BookCopy` | Completed |
| `fines` table exists with PK `fine_id` | Completed |
| `fines.borrow_id` connects to `borrow_records.borrow_id` | Completed |
| `fines.member_id` connects to `members.member_id` | Completed |
| `notifications` table exists with PK `notification_id` | Completed |
| `notifications.member_id` connects to `members.member_id` | Completed |
| Notifications do not connect directly to `users` | Completed |
| `reports` table exists with PK `report_id` | Completed |
| `reports.generated_by` connects to `users.user_id` | Completed |
| Extra prohibited domain models are not installed in the active app | Completed |

## 4. How To Run The Project

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

Apply database migrations:

```bash
python3 manage.py migrate
```

Start the development server:

```bash
python3 manage.py runserver
```

Open:

- Application: `http://127.0.0.1:8000/`
- Admin panel: `http://127.0.0.1:8000/admin/`

## 5. How To Load Sample Data

Run:

```bash
python3 manage.py seed_data
```

Optional custom password:

```bash
python3 manage.py seed_data --password YourPassword@123
```

Default sample accounts:

| Username | Password | Role |
| --- | --- | --- |
| `sample_admin` | `Library@123` | Super Admin |
| `sample_librarian` | `Library@123` | Librarian |
| `sample_assistant` | `Library@123` | Assistant Librarian |
| `sample_student` | `Library@123` | Student |
| `sample_teacher` | `Library@123` | Teacher |
| `sample_staff` | `Library@123` | Staff |

The seed command creates valid rows for all 11 tables: roles, users, categories, authors, publishers, books, members, borrow records, fines, notifications, and reports.

## 6. How To Test The System

Run:

```bash
python3 manage.py test
```

Recommended manual testing flow:

1. Log in as `sample_admin`.
2. Open the dashboard and check statistics.
3. Add, edit, and delete roles, users, categories, authors, publishers, and members.
4. Add a new book and verify stock fields.
5. Borrow an available book.
6. Confirm the selected book's available quantity decreases.
7. Return the borrowed book.
8. Confirm `received_by`, `return_date`, book stock, and status update.
9. Return a late book and verify fine creation.
10. Pay a fine and verify paid amount and balance.
11. Create a notification and confirm it appears in member notification history.
12. Generate a report and verify it appears in the reports list.

Automated tests cover:

- All 11 required tables.
- Correct `db_table` names.
- Correct primary key names.
- Borrow records connected to `books`, `members`, `issued_by`, and `received_by`.
- Fines connected to `borrow_records` and `members`.
- Notifications connected to `members`.
- Reports connected to generated-by users.
- Borrow workflow.
- Return workflow.
- Fine calculation.
- Notification creation.
- Report generation.
- Repeatable seed data.

## 7. Main Features Completed

- Custom `users` model using the lecturer `users` table.
- Role management using the `roles` table.
- Book master data: categories, authors, publishers, and books.
- Member management.
- Borrow book workflow.
- Return book workflow.
- Automatic stock update during borrowing and returning.
- Automatic fine calculation for late returns.
- Fine payment tracking.
- Member notification history.
- CSV report generation and report history.
- Bootstrap 5 templates.
- Django Admin configuration for all 11 required models.
- Sample data command.
- Automated test suite.

## 8. Screenshots Checklist

Capture the following screenshots for the final report:

- Login page.
- Dashboard statistics.
- Role list page.
- User list page.
- Category list page.
- Author list page.
- Publisher list page.
- Book list page.
- Add/edit book form.
- Member list page.
- Borrow book form.
- Borrow records list.
- Return book form.
- Fine list page.
- Fine payment form.
- Notification list page.
- Report list page.
- Generated report file in `media/reports/`.
- Django Admin model list.
- Terminal showing `python3 manage.py test` passing.
- Terminal showing `python3 manage.py seed_data` success.

## 9. Final Presentation Outline

1. Title slide: Library Management System.
2. Problem statement: manual library work causes slow processing and record errors.
3. Objectives: accurate book, member, borrow, return, fine, notification, and report management.
4. Technology stack: Django, SQLite, Bootstrap 5.
5. Corrected Data Dictionary: 11 required tables.
6. ERD explanation: users, members, books, borrow records, fines, notifications, reports.
7. System architecture: one active Django app, reusable forms, views, templates, and admin.
8. Main features demonstration.
9. Borrowing workflow demonstration.
10. Returning and fine calculation demonstration.
11. Notification and report demonstration.
12. Testing result.
13. Security and validation.
14. Challenges and fixes: replacing wrong multi-app schema with corrected Data Dictionary schema.
15. Future improvements.
16. Conclusion.

## 10. Lecturer Submission Checklist

Before submitting, confirm:

- `apps/library/models.py` contains the corrected 11-table schema.
- `config/settings.py` installs `apps.library.apps.LibraryConfig`.
- `AUTH_USER_MODEL = "library.User"` is configured.
- `python3 manage.py makemigrations` reports no unexpected schema drift.
- `python3 manage.py migrate` completes successfully.
- `python3 manage.py seed_data` creates sample data successfully.
- `python3 manage.py test` passes.
- Dashboard loads correctly.
- Login works for sample admin account.
- Borrowing flow works.
- Return flow works.
- Fine calculation works.
- Notifications connect to members.
- Reports connect to generated-by users.
- Screenshots are prepared.
- README is included.
- Final documentation is included.
- Source code is zipped with required files only for submission.

## Future Improvement Suggestions

- Add barcode or QR code printing for books.
- Add email reminders for due dates.
- Add PDF report export.
- Add Excel import/export for books and members.
- Add advanced dashboard charts.
- Add PostgreSQL deployment profile.
- Add role permission screens for more detailed access control.
- Add backup and restore features.
- Add audit logging for sensitive actions.

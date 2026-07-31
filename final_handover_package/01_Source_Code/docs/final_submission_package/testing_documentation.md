# Testing Documentation

Project: Enterprise Library Management System  
Testing scope: Corrected 11-table Django implementation

## 1. Test Plan

### 1.1 Testing Objectives

The testing objectives are:

1. Verify the system follows the lecturer's 11-table Data Dictionary.
2. Verify all required relationships are correct.
3. Verify the borrowing workflow.
4. Verify the returning workflow.
5. Verify fine calculation.
6. Verify notification creation.
7. Verify report generation.
8. Verify authentication and permission behavior.
9. Verify sample data can be loaded.
10. Verify the system has no migration drift.

### 1.2 Testing Types

| Testing Type | Purpose |
| --- | --- |
| Unit testing | Test models and small logic |
| Integration testing | Test workflows across models, forms, and views |
| Schema testing | Verify table names, primary keys, and relationships |
| Permission testing | Verify staff and member access |
| Smoke testing | Verify important pages load |
| Data testing | Verify seed data creates all required records |

### 1.3 Test Environment

| Item | Value |
| --- | --- |
| Framework | Django |
| Database | SQLite |
| Test command | `python3 manage.py test` |
| Application app | `apps.library` |
| Test runner | Django test framework |

## 2. Test Cases

### TC-001: Required Table Names

Objective: Confirm all table names match the lecturer Data Dictionary.

Expected result:

- `roles`
- `users`
- `categories`
- `authors`
- `publishers`
- `books`
- `members`
- `borrow_records`
- `fines`
- `notifications`
- `reports`

Actual result: Passed.

### TC-002: Required Primary Keys

Objective: Confirm all primary key names match the lecturer Data Dictionary.

Expected result:

- `role_id`
- `user_id`
- `category_id`
- `author_id`
- `publisher_id`
- `book_id`
- `member_id`
- `borrow_id`
- `fine_id`
- `notification_id`
- `report_id`

Actual result: Passed.

### TC-003: BorrowRecord Uses Book

Objective: Confirm borrow records connect directly to books.

Expected result:

- `BorrowRecord.book` references `Book`.
- No `book_copy` field is used.

Actual result: Passed.

### TC-004: BorrowRecord Staff Users

Objective: Confirm borrow records include issuing and receiving users.

Expected result:

- `issued_by` references `User`.
- `received_by` references `User`.

Actual result: Passed.

### TC-005: Notification Relationship

Objective: Confirm notifications connect to members.

Expected result:

- `Notification.member` references `Member`.

Actual result: Passed.

### TC-006: Report Relationship

Objective: Confirm reports connect to generated-by user.

Expected result:

- `Report.generated_by` references `User`.

Actual result: Passed.

### TC-007: Create Valid Records For All 11 Tables

Objective: Confirm each required table accepts valid records.

Expected result:

- Records are created successfully in all 11 tables.

Actual result: Passed.

### TC-008: Borrow Book Workflow

Objective: Confirm book issue works.

Steps:

1. Log in as admin.
2. Select active member.
3. Select available book.
4. Submit borrow form.

Expected result:

- Borrow record is created.
- `issued_by` is logged-in user.
- Book available quantity decreases.

Actual result: Passed.

### TC-009: Return Book Workflow

Objective: Confirm book return works.

Steps:

1. Log in as admin.
2. Open active borrow record.
3. Enter return date.
4. Submit return form.

Expected result:

- Status changes to Returned.
- `received_by` is logged-in user.
- Return date is saved.
- Book available quantity increases.

Actual result: Passed.

### TC-010: Fine Calculation

Objective: Confirm late return creates correct fine.

Expected result:

- Late days are calculated.
- Fine amount equals late days multiplied by 1.00.

Actual result: Passed.

### TC-011: Notification Creation

Objective: Confirm late return creates notification.

Expected result:

- Notification is connected to member.
- Notification type is Fine.

Actual result: Passed.

### TC-012: Report Generation

Objective: Confirm report generation records user and file.

Expected result:

- Report row is created.
- `generated_by` is logged-in user.
- CSV file is generated.

Actual result: Passed.

### TC-013: Staff Page Access

Objective: Confirm staff can access management pages.

Expected result:

- Dashboard, books, borrowing, fines, notifications, reports, and master data pages return HTTP 200.

Actual result: Passed.

### TC-014: Member Notification Privacy

Objective: Confirm members see only their own notifications.

Expected result:

- Member sees own notification.
- Member does not see another member's notification.

Actual result: Passed.

### TC-015: Non-Staff Access Restriction

Objective: Confirm non-staff users cannot access master data management.

Expected result:

- Non-staff user is redirected.

Actual result: Passed.

### TC-016: Seed Data Command

Objective: Confirm sample data command creates valid records.

Expected result:

- All 11 tables receive sample rows.
- Command can be run repeatedly without creating duplicates.

Actual result: Passed.

## 3. Test Results

Latest automated test command:

```bash
python3 manage.py test
```

Result:

```text
Ran 12 tests
OK
```

System check:

```bash
python3 manage.py check
```

Result:

```text
System check identified no issues
```

Migration drift:

```bash
python3 manage.py makemigrations --check --dry-run
```

Result:

```text
No changes detected
```

Database integrity:

```text
FOREIGN_KEY_CHECK OK
INTEGRITY_CHECK ok
```

## 4. Bug Fix Summary

| Issue | Fix | Status |
| --- | --- | --- |
| Wrong earlier schema used many extra apps and tables | Replaced active schema with one corrected `apps.library` app | Fixed |
| Borrow record used BookCopy in earlier design | Corrected BorrowRecord to use `book_id` FK to `books` | Fixed |
| Borrow record needed staff tracking | Added `issued_by` and `received_by` FKs to `users` | Fixed |
| Notifications connected to wrong target in earlier design | Corrected Notification to use `member_id` FK to `members` | Fixed |
| Report table missing | Added `reports` table with `generated_by` FK to `users` | Fixed |
| Need repeatable demo data | Added `seed_data` management command | Fixed |
| Test client host issue during audit | Added `testserver` to allowed hosts | Fixed |
| Minor admin N+1 risk | Improved admin `list_select_related` | Fixed |

## 5. Manual Testing Checklist

Before presentation, manually verify:

- Login with `sample_admin`.
- Login with `sample_student`.
- Open dashboard.
- Add or edit a role.
- Add or edit a user.
- Add or edit a member.
- Add or edit a book.
- Borrow an available book.
- Return a borrowed book.
- Return a late book and check fine.
- Pay a fine.
- Create a notification.
- Generate a report.
- Confirm non-staff cannot access staff-only pages.

## 6. Testing Conclusion

The corrected Library Management System passed automated and manual audit testing. The most important workflows work correctly, and the system matches the lecturer's required 11-table database structure.

# Database Submission Guide

## Database Status

- Database provider: Supabase PostgreSQL
- Authentication provider: Supabase Auth
- Django business tables: 11 required tables
- Schema status: lecturer data dictionary preserved
- Secret handling: no real passwords or keys included in this package

## Final 11-Table Data Dictionary

### 1. roles

Primary key: `role_id`

| Field | Type | Notes |
| --- | --- | --- |
| role_id | BigAutoField | Primary key |
| role_name | CharField(50) | Unique role name |
| description | TextField | Optional description |

### 2. users

Primary key: `user_id`

| Field | Type | Notes |
| --- | --- | --- |
| user_id | BigAutoField | Primary key |
| role_id | ForeignKey roles.role_id | Protected role relationship |
| username | CharField(50) | Unique |
| email | EmailField(100) | Unique; synced with Supabase Auth email |
| full_name | CharField(100) | User full name |
| phone | CharField(20) | Optional |
| address | TextField | Optional |
| is_active | BooleanField | Blocks inactive users |
| is_staff | BooleanField | Django admin/staff access |
| is_superuser | BooleanField | Full Django permissions |
| created_at | DateTimeField | Created timestamp |
| updated_at | DateTimeField | Updated timestamp |

### 3. categories

Primary key: `category_id`

| Field | Type | Notes |
| --- | --- | --- |
| category_id | BigAutoField | Primary key |
| category_name | CharField(100) | Unique |
| description | TextField | Optional |

### 4. authors

Primary key: `author_id`

| Field | Type | Notes |
| --- | --- | --- |
| author_id | BigAutoField | Primary key |
| author_name | CharField(100) | Author name |
| biography | TextField | Optional |

### 5. publishers

Primary key: `publisher_id`

| Field | Type | Notes |
| --- | --- | --- |
| publisher_id | BigAutoField | Primary key |
| publisher_name | CharField(100) | Unique |
| address | TextField | Optional |
| contact_number | CharField(20) | Optional |
| email | EmailField(100) | Optional |

### 6. books

Primary key: `book_id`

| Field | Type | Notes |
| --- | --- | --- |
| book_id | BigAutoField | Primary key |
| category_id | ForeignKey categories.category_id | Protected relationship |
| author_id | ForeignKey authors.author_id | Protected relationship |
| publisher_id | ForeignKey publishers.publisher_id | Protected relationship |
| isbn | CharField(20) | Unique |
| title | CharField(200) | Book title |
| edition | CharField(50) | Optional |
| publication_year | PositiveSmallIntegerField | Optional, 1000-9999 |
| quantity | PositiveIntegerField | Total stock |
| available_quantity | PositiveIntegerField | Available stock |
| shelf_location | CharField(100) | Optional |
| status | CharField(20) | available, borrowed, lost, damaged, under_repair |
| created_at | DateTimeField | Created timestamp |
| updated_at | DateTimeField | Updated timestamp |

### 7. members

Primary key: `member_id`

| Field | Type | Notes |
| --- | --- | --- |
| member_id | BigAutoField | Primary key |
| user_id | OneToOne users.user_id | Member user account |
| member_code | CharField(30) | Unique |
| member_type | CharField(20) | student, teacher, staff, librarian |
| department | CharField(100) | Optional |
| phone | CharField(20) | Optional |
| address | TextField | Optional |
| registration_date | DateField | Registration date |
| status | CharField(20) | active, suspended, expired |

### 8. borrow_records

Primary key: `borrow_id`

| Field | Type | Notes |
| --- | --- | --- |
| borrow_id | BigAutoField | Primary key |
| member_id | ForeignKey members.member_id | Borrowing member |
| book_id | ForeignKey books.book_id | Borrowed book |
| issued_by | ForeignKey users.user_id | User who issued the book |
| received_by | ForeignKey users.user_id | Nullable user who received return |
| borrow_date | DateField | Borrow date |
| due_date | DateField | Due date |
| return_date | DateField | Nullable return date |
| status | CharField(20) | borrowed, returned, overdue, lost |

### 9. fines

Primary key: `fine_id`

| Field | Type | Notes |
| --- | --- | --- |
| fine_id | BigAutoField | Primary key |
| borrow_id | ForeignKey borrow_records.borrow_id | Fine source transaction |
| member_id | ForeignKey members.member_id | Fine owner |
| amount | DecimalField(10,2) | Fine amount |
| paid_amount | DecimalField(10,2) | Paid amount |
| status | CharField(20) | unpaid, partially_paid, paid, waived |
| created_at | DateTimeField | Created timestamp |
| paid_date | DateTimeField | Nullable paid timestamp |

### 10. notifications

Primary key: `notification_id`

| Field | Type | Notes |
| --- | --- | --- |
| notification_id | BigAutoField | Primary key |
| member_id | ForeignKey members.member_id | Notification recipient |
| title | CharField(150) | Notification title |
| message | TextField | Notification message |
| notification_type | CharField(20) | due_date, overdue, fine, general |
| is_read | BooleanField | Read status |
| created_at | DateTimeField | Created timestamp |

### 11. reports

Primary key: `report_id`

| Field | Type | Notes |
| --- | --- | --- |
| report_id | BigAutoField | Primary key |
| report_type | CharField(30) | books, members, borrowing, fines |
| generated_by | ForeignKey users.user_id | Report creator |
| generated_at | DateTimeField | Generated timestamp |
| file_path | FileField | Optional generated report file |

## Relationship Summary

- `users.role_id` references `roles.role_id`
- `books.category_id` references `categories.category_id`
- `books.author_id` references `authors.author_id`
- `books.publisher_id` references `publishers.publisher_id`
- `members.user_id` references `users.user_id`
- `borrow_records.member_id` references `members.member_id`
- `borrow_records.book_id` references `books.book_id`
- `borrow_records.issued_by` references `users.user_id`
- `borrow_records.received_by` references `users.user_id`
- `fines.borrow_id` references `borrow_records.borrow_id`
- `fines.member_id` references `members.member_id`
- `notifications.member_id` references `members.member_id`
- `reports.generated_by` references `users.user_id`

## Supabase Verification Queries

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
and table_name in (
  'roles', 'users', 'categories', 'authors', 'publishers',
  'books', 'members', 'borrow_records', 'fines',
  'notifications', 'reports'
)
order by table_name;
```

```sql
select
  tc.table_name,
  kcu.column_name,
  ccu.table_name as foreign_table_name,
  ccu.column_name as foreign_column_name
from information_schema.table_constraints as tc
join information_schema.key_column_usage as kcu
  on tc.constraint_name = kcu.constraint_name
join information_schema.constraint_column_usage as ccu
  on ccu.constraint_name = tc.constraint_name
where tc.constraint_type = 'FOREIGN KEY'
and tc.table_schema = 'public'
order by tc.table_name, kcu.column_name;
```

## Safe PostgreSQL Schema Export

Do not place real passwords in this document. Run export commands from a secure terminal using environment variables.

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
pg_dump "$DATABASE_URL" --schema-only --file library_schema.sql
```

## Sample Data Export

```bash
pg_dump "$DATABASE_URL" \
  --data-only \
  --table=roles \
  --table=users \
  --table=categories \
  --table=authors \
  --table=publishers \
  --table=books \
  --table=members \
  --table=borrow_records \
  --table=fines \
  --table=notifications \
  --table=reports \
  --file library_sample_data.sql
```

## Restore Command

Restore only to a test database unless production recovery is required.

```bash
psql "$DATABASE_URL" --file library_schema.sql
psql "$DATABASE_URL" --file library_sample_data.sql
```

## Backup Security Rules

- Never include real database passwords in exported files.
- Store backups in a private secure location.
- Do not commit SQL dumps with real user/member data to GitHub.
- Encrypt backups before cloud upload.
- Verify restore on a temporary database before using production.

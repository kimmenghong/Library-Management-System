# Database Documentation

Project: Enterprise Library Management System  
Database: SQLite development database  
Schema: Corrected 11-table lecturer Data Dictionary

## 1. Final Data Dictionary

The active application schema contains exactly 11 Library Management System tables.

## 2. Table: roles

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `role_id` | BigAutoField | PK | Unique role ID |
| `role_name` | CharField(50) | Unique | Name of the role |
| `description` | TextField |  | Role description |

Purpose: stores user role information.

## 3. Table: users

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `user_id` | BigAutoField | PK | Unique user ID |
| `role_id` | ForeignKey | FK | References `roles.role_id` |
| `username` | CharField(50) | Unique | Login username |
| `email` | EmailField(100) | Unique | User email |
| `full_name` | CharField(100) |  | User full name |
| `phone` | CharField(20) |  | Phone number |
| `address` | TextField |  | User address |
| `is_active` | BooleanField |  | Whether the user can log in |
| `is_staff` | BooleanField |  | Whether the user can access staff features |
| `is_superuser` | BooleanField |  | Whether the user has full admin access |
| `created_at` | DateTimeField |  | Created timestamp |
| `updated_at` | DateTimeField |  | Updated timestamp |

Purpose: stores login accounts and user identity data.

## 4. Table: categories

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `category_id` | BigAutoField | PK | Unique category ID |
| `category_name` | CharField(100) | Unique | Category name |
| `description` | TextField |  | Category description |

Purpose: groups books by category.

## 5. Table: authors

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `author_id` | BigAutoField | PK | Unique author ID |
| `author_name` | CharField(100) |  | Author name |
| `biography` | TextField |  | Author biography |

Purpose: stores author information.

## 6. Table: publishers

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `publisher_id` | BigAutoField | PK | Unique publisher ID |
| `publisher_name` | CharField(100) | Unique | Publisher name |
| `address` | TextField |  | Publisher address |
| `contact_number` | CharField(20) |  | Publisher contact number |
| `email` | EmailField(100) |  | Publisher email |

Purpose: stores publisher information.

## 7. Table: books

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `book_id` | BigAutoField | PK | Unique book ID |
| `category_id` | ForeignKey | FK | References `categories.category_id` |
| `author_id` | ForeignKey | FK | References `authors.author_id` |
| `publisher_id` | ForeignKey | FK | References `publishers.publisher_id` |
| `isbn` | CharField(20) | Unique | Book ISBN |
| `title` | CharField(200) |  | Book title |
| `edition` | CharField(50) |  | Book edition |
| `publication_year` | PositiveSmallIntegerField |  | Publication year |
| `quantity` | PositiveIntegerField |  | Total quantity |
| `available_quantity` | PositiveIntegerField |  | Available quantity |
| `shelf_location` | CharField(100) |  | Shelf or location |
| `status` | CharField(20) |  | Book status |
| `created_at` | DateTimeField |  | Created timestamp |
| `updated_at` | DateTimeField |  | Updated timestamp |

Purpose: stores book catalog and stock data.

Book status values:

- `available`
- `borrowed`
- `lost`
- `damaged`
- `under_repair`

## 8. Table: members

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `member_id` | BigAutoField | PK | Unique member ID |
| `user_id` | OneToOneField | FK | References `users.user_id` |
| `member_code` | CharField(30) | Unique | Member code |
| `member_type` | CharField(20) |  | Student, teacher, staff, or librarian |
| `department` | CharField(100) |  | Department |
| `phone` | CharField(20) |  | Member phone |
| `address` | TextField |  | Member address |
| `registration_date` | DateField |  | Registration date |
| `status` | CharField(20) |  | Member status |

Purpose: stores library member profiles.

Member types:

- `student`
- `teacher`
- `staff`
- `librarian`

Member statuses:

- `active`
- `suspended`
- `expired`

## 9. Table: borrow_records

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `borrow_id` | BigAutoField | PK | Unique borrow record ID |
| `member_id` | ForeignKey | FK | References `members.member_id` |
| `book_id` | ForeignKey | FK | References `books.book_id` |
| `issued_by` | ForeignKey | FK | References `users.user_id` |
| `received_by` | ForeignKey | FK | References `users.user_id`; nullable |
| `borrow_date` | DateField |  | Borrow date |
| `due_date` | DateField |  | Due date |
| `return_date` | DateField |  | Return date; nullable |
| `status` | CharField(20) |  | Borrow status |

Purpose: stores book borrowing and returning records.

Important correction:

- `borrow_records.book_id` references `books.book_id` directly.
- It does not reference `BookCopy`.

Borrow statuses:

- `borrowed`
- `returned`
- `overdue`
- `lost`

## 10. Table: fines

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `fine_id` | BigAutoField | PK | Unique fine ID |
| `borrow_id` | ForeignKey | FK | References `borrow_records.borrow_id` |
| `member_id` | ForeignKey | FK | References `members.member_id` |
| `amount` | DecimalField(10,2) |  | Total fine amount |
| `paid_amount` | DecimalField(10,2) |  | Paid amount |
| `status` | CharField(20) |  | Fine status |
| `created_at` | DateTimeField |  | Created timestamp |
| `paid_date` | DateTimeField |  | Paid timestamp |

Purpose: stores late return fines and payment status.

Fine statuses:

- `unpaid`
- `partially_paid`
- `paid`
- `waived`

## 11. Table: notifications

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `notification_id` | BigAutoField | PK | Unique notification ID |
| `member_id` | ForeignKey | FK | References `members.member_id` |
| `title` | CharField(150) |  | Notification title |
| `message` | TextField |  | Notification message |
| `notification_type` | CharField(20) |  | Notification type |
| `is_read` | BooleanField |  | Read status |
| `created_at` | DateTimeField |  | Created timestamp |

Purpose: stores member notification history.

Important correction:

- Notifications connect to members, not directly to users.

Notification types:

- `due_date`
- `overdue`
- `fine`
- `general`

## 12. Table: reports

| Field | Type | Key | Description |
| --- | --- | --- | --- |
| `report_id` | BigAutoField | PK | Unique report ID |
| `report_type` | CharField(30) |  | Report type |
| `generated_by` | ForeignKey | FK | References `users.user_id` |
| `generated_at` | DateTimeField |  | Generated timestamp |
| `file_path` | FileField |  | Report file path |

Purpose: stores generated report history.

Report types:

- `books`
- `members`
- `borrowing`
- `fines`

## 13. Table Relationships

| Relationship | Type |
| --- | --- |
| `roles` to `users` | One-to-many |
| `users` to `members` | One-to-one |
| `categories` to `books` | One-to-many |
| `authors` to `books` | One-to-many |
| `publishers` to `books` | One-to-many |
| `members` to `borrow_records` | One-to-many |
| `books` to `borrow_records` | One-to-many |
| `users` to `borrow_records.issued_by` | One-to-many |
| `users` to `borrow_records.received_by` | One-to-many |
| `borrow_records` to `fines` | One-to-many |
| `members` to `fines` | One-to-many |
| `members` to `notifications` | One-to-many |
| `users` to `reports` | One-to-many |

## 14. Foreign Keys

| Table | Foreign Key | References |
| --- | --- | --- |
| `users` | `role_id` | `roles.role_id` |
| `books` | `category_id` | `categories.category_id` |
| `books` | `author_id` | `authors.author_id` |
| `books` | `publisher_id` | `publishers.publisher_id` |
| `members` | `user_id` | `users.user_id` |
| `borrow_records` | `member_id` | `members.member_id` |
| `borrow_records` | `book_id` | `books.book_id` |
| `borrow_records` | `issued_by` | `users.user_id` |
| `borrow_records` | `received_by` | `users.user_id` |
| `fines` | `borrow_id` | `borrow_records.borrow_id` |
| `fines` | `member_id` | `members.member_id` |
| `notifications` | `member_id` | `members.member_id` |
| `reports` | `generated_by` | `users.user_id` |

## 15. Constraints

| Constraint | Description |
| --- | --- |
| Unique role name | Each role name is unique |
| Unique username | Each login username is unique |
| Unique email | Each user email is unique |
| Unique category name | Each category name is unique |
| Unique publisher name | Each publisher name is unique |
| Unique ISBN | Each book ISBN is unique |
| Unique member code | Each member code is unique |
| Quantity non-negative | Book quantity cannot be negative |
| Available quantity non-negative | Book available quantity cannot be negative |
| Available quantity not above quantity | Available quantity cannot exceed total quantity |
| Due date validation | Due date cannot be earlier than borrow date |
| Return date validation | Return date cannot be earlier than borrow date |
| Fine amount non-negative | Fine amount cannot be negative |
| Paid amount valid | Paid amount cannot be negative or greater than amount |

## 16. Indexes

Django automatically creates indexes for:

- Primary keys
- Unique fields
- Foreign keys

Important indexed fields include:

- `roles.role_id`
- `users.user_id`
- `users.role_id`
- `categories.category_id`
- `authors.author_id`
- `publishers.publisher_id`
- `books.book_id`
- `books.category_id`
- `books.author_id`
- `books.publisher_id`
- `members.member_id`
- `members.user_id`
- `borrow_records.borrow_id`
- `borrow_records.member_id`
- `borrow_records.book_id`
- `borrow_records.issued_by`
- `borrow_records.received_by`
- `fines.fine_id`
- `fines.borrow_id`
- `fines.member_id`
- `notifications.notification_id`
- `notifications.member_id`
- `reports.report_id`
- `reports.generated_by`

Future performance indexes may be added for:

- `books.status`
- `borrow_records.status`
- `borrow_records.due_date`
- `fines.status`
- `notifications.is_read`

## 17. Database Verification Result

Latest audit result:

```text
MODEL_COUNT 11
FOREIGN_KEY_CHECK OK
INTEGRITY_CHECK ok
```

All active application models match the lecturer's required table names and primary key names.

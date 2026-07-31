# Viva / Defense Preparation

Project: Enterprise Library Management System

## 1. Project Strengths

- Corrected to match the lecturer's 11-table Data Dictionary exactly.
- Uses Django best practices: models, forms, views, templates, admin, migrations, tests.
- Includes authentication and role-based access behavior.
- Supports the main library workflows: books, members, borrowing, returning, fines, notifications, and reports.
- Uses database constraints and model validation.
- Includes sample data command.
- Includes automated tests.
- Includes final documentation package.
- Clear separation between active corrected app and inactive legacy phase files.

## 2. Project Limitations

- Reservations are not implemented because the corrected Data Dictionary does not include a reservations table.
- Active API endpoints are not included in the corrected 11-table version.
- Email reminders are not active.
- PDF and Excel report exports are future improvements.
- Backup and restore are handled administratively, not through a database module.
- The system uses SQLite for development; production should use PostgreSQL or MySQL.
- Long list pages can later be improved with pagination.

## 3. Future Enhancements

- Add reservation module with a new reservations table.
- Add barcode and QR code support.
- Add email reminders for due and overdue books.
- Add PDF and Excel export.
- Add REST API using Django REST Framework.
- Add dashboard charts.
- Add audit trail.
- Add backup and restore module.
- Add advanced search and filters.
- Add member self-service portal.

## 4. 50 Possible Examiner Questions With Professional Answers

### 1. What is your project about?

It is a Django-based Library Management System that manages users, roles, books, members, borrowing, returning, fines, notifications, and reports.

### 2. What problem does your system solve?

It reduces manual library work, improves record accuracy, tracks borrowing and returning, calculates fines, and helps staff generate reports.

### 3. What technology did you use?

I used Python Django for the backend, SQLite for development database, and HTML, CSS, Bootstrap 5 for the frontend.

### 4. Why did you choose Django?

Django provides authentication, admin, ORM, form validation, templates, migrations, and testing, which are very useful for a database management system.

### 5. What database did you use?

I used SQLite for development. The system can be adapted to PostgreSQL or MySQL for deployment.

### 6. How many application tables are in the final system?

The final active system has exactly 11 application tables according to the lecturer's Data Dictionary.

### 7. What are the 11 tables?

The tables are roles, users, categories, authors, publishers, books, members, borrow_records, fines, notifications, and reports.

### 8. Why did you remove extra tables from the earlier design?

The lecturer required a specific 11-table Data Dictionary, so I corrected the active schema to match that exactly.

### 9. What is the purpose of the roles table?

The roles table stores role names and descriptions. Users are assigned to roles.

### 10. What is the purpose of the users table?

The users table stores login accounts, contact details, role, and access flags such as active, staff, and superuser.

### 11. What is the purpose of the books table?

The books table stores catalog and stock information such as title, ISBN, author, category, publisher, quantity, available quantity, shelf location, and status.

### 12. What is the purpose of the members table?

The members table stores library member profiles and connects each member to a user account.

### 13. What is the central transaction table?

The central transaction table is borrow_records because it connects members, books, issued_by user, and received_by user.

### 14. Why does BorrowRecord use book_id instead of BookCopy?

Because the lecturer required `borrow_records.book_id` to reference `books`. The corrected final implementation follows that requirement.

### 15. What does issued_by mean?

`issued_by` stores the user who issued the book to the member.

### 16. What does received_by mean?

`received_by` stores the user who received the returned book.

### 17. How does the system prevent borrowing unavailable books?

The borrow form only selects books with available quantity greater than zero and status Available. The view also checks availability before saving.

### 18. What happens when a book is borrowed?

A borrow record is created, the logged-in staff user is saved as issued_by, and the book's available quantity decreases.

### 19. What happens when a book is returned?

The borrow record is updated with return date and received_by, status becomes Returned, and book available quantity increases.

### 20. How does fine calculation work?

The system calculates late days by comparing return date with due date. The fine is late days multiplied by 1.00.

### 21. Where are fines stored?

Fines are stored in the fines table and connected to both borrow_records and members.

### 22. Why does Fine connect to Member and BorrowRecord?

BorrowRecord explains which borrowing transaction caused the fine, and Member identifies who must pay it.

### 23. Where are notifications stored?

Notifications are stored in the notifications table.

### 24. Why does Notification connect to Member?

The lecturer required notifications to connect to members. This also makes sense because notifications belong to member history.

### 25. What is the purpose of reports table?

The reports table stores report type, generated file path, generated date, and the user who generated the report.

### 26. What is generated_by?

`generated_by` is a foreign key to users and stores who generated a report.

### 27. How did you verify the database design?

I wrote automated tests for table names, primary key names, and foreign key relationships. I also ran migration and database integrity checks.

### 28. What tests did you run?

I ran Django system checks, migration drift checks, the full Django test suite, database integrity checks, and manual page smoke tests.

### 29. What was the test result?

The latest test result was 12 tests passed successfully.

### 30. What is the role of Django Admin?

Django Admin allows administrators to manage records for all 11 active models.

### 31. How is security handled?

The system uses Django authentication, CSRF middleware, password hashing, session protection, staff-only view decorators, and environment-based settings.

### 32. What should be changed before production deployment?

Set `DEBUG=False`, use a strong secret key, enable HTTPS settings, use secure cookies, configure allowed hosts, and use a production database.

### 33. Does the system support backup and restore?

Backup and restore are handled administratively by copying the SQLite database and media files. A full backup module can be added later.

### 34. Does the system support reservations?

No. Reservations are listed as a future improvement because the corrected 11-table Data Dictionary does not include a reservations table.

### 35. Does the system support API endpoints?

The corrected final version does not expose active API routes. API endpoints can be added later based on the corrected 11-table models.

### 36. What is the difference between quantity and available_quantity?

Quantity is total stock for a book. Available quantity is the number currently available to borrow.

### 37. What happens if available quantity becomes zero?

The book status can become Borrowed, meaning it is not currently available for issue.

### 38. How do you protect historical data?

Foreign keys use protected relationships where important history should not be deleted accidentally. For example, books with borrowing history cannot be deleted.

### 39. What is the purpose of seed_data?

It creates sample roles, users, categories, authors, publishers, books, members, borrow records, fines, notifications, and reports.

### 40. Can seed_data be run more than once?

Yes. The command is repeatable and avoids duplicate sample records.

### 41. How do members see their notifications?

Members log in and open the Notifications page. The system filters notifications to their member profile.

### 42. Can students manage users?

No. User management is restricted to staff-level users.

### 43. What is the dashboard used for?

The dashboard summarizes library statistics and recent borrowing activity.

### 44. What report formats are supported?

The active corrected system generates CSV report files.

### 45. Why not include every feature from the earlier enterprise plan?

Because the final correction required matching the lecturer's 11-table Data Dictionary exactly. Extra features would require extra tables.

### 46. What is your biggest challenge?

The biggest challenge was correcting the earlier multi-app schema into the exact 11-table Data Dictionary without breaking the core workflows.

### 47. What is your best technical achievement?

The best achievement is a working corrected schema with proper relationships, validation, tests, sample data, and documentation.

### 48. How would you improve performance?

I would add pagination, add indexes for frequently filtered fields, and use select_related and prefetch_related where needed.

### 49. How would you improve security?

I would enforce HTTPS, use production secret settings, add more granular permissions, and add audit logs.

### 50. Is the project ready for submission?

Yes. The active corrected system is ready for university submission after excluding or archiving inactive legacy phase files.

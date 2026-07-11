# Presentation Package

Project: Enterprise Library Management System  
Presentation length: 10 to 15 minutes

## 1. 15-Slide Presentation Outline

### Slide 1: Title Slide

Title: Enterprise Library Management System  
Subtitle: Django-Based University Final Project  
Include:

- Student name
- Student ID
- Lecturer name
- Department
- Date

Presenter notes:

Introduce yourself and state that the project is a corrected Django Library Management System based on the lecturer's 11-table Data Dictionary.

### Slide 2: Problem Statement

Main points:

- Manual library records are slow.
- Paper records can be lost or duplicated.
- Borrowing and returning need accurate tracking.
- Fine calculation is difficult manually.
- Reports take time to prepare.

Presenter notes:

Explain that the system solves common library management problems by storing data in a structured database.

### Slide 3: Project Objectives

Main points:

- Manage books, members, users, and roles.
- Record borrowing and returning.
- Calculate late return fines.
- Store member notifications.
- Generate reports.
- Follow the lecturer's required 11-table schema.

Presenter notes:

Emphasize that the project objective is not only to build features, but also to follow the required database design correctly.

### Slide 4: Technology Stack

Main points:

- Python
- Django
- SQLite
- HTML, CSS, Bootstrap 5
- Django Admin
- Django test framework

Presenter notes:

Explain why Django is suitable: built-in authentication, admin, ORM, forms, templates, and testing.

### Slide 5: System Architecture

Main points:

- Browser
- Django URL router
- Views
- Forms
- Models
- Templates
- SQLite database

Presenter notes:

Describe the flow from user request to database and back to HTML response.

### Slide 6: Final 11-Table Data Dictionary

Main points:

- roles
- users
- categories
- authors
- publishers
- books
- members
- borrow_records
- fines
- notifications
- reports

Presenter notes:

State clearly that the final corrected implementation uses exactly these 11 application tables.

### Slide 7: ER Diagram And Relationships

Main points:

- Roles connect to users.
- Users connect to members.
- Books connect to categories, authors, and publishers.
- Borrow records connect members, books, issued_by, and received_by.
- Fines connect borrow records and members.
- Notifications connect members.
- Reports connect generated_by user.

Presenter notes:

Explain that the borrow record is the central transaction table.

### Slide 8: Authentication And Roles

Main points:

- Login and logout.
- Role-based access.
- Staff access for management pages.
- Member access to own data.

Presenter notes:

Mention that user access is controlled through role and staff status.

### Slide 9: Book And Member Management

Main points:

- Add, edit, delete books.
- Manage categories, authors, publishers.
- Manage member profiles.
- Search and filter books.

Presenter notes:

Show how the system supports library master data management.

### Slide 10: Borrowing Workflow

Main points:

- Select member.
- Select available book.
- Enter borrow date and due date.
- Save borrow record.
- Update book availability.
- Store `issued_by`.

Presenter notes:

Explain that the system prevents unavailable books from being borrowed.

### Slide 11: Returning And Fine Workflow

Main points:

- Enter return date.
- Store `received_by`.
- Update borrow status.
- Increase book availability.
- Calculate fine for late return.
- Create notification.

Presenter notes:

Use an example: 5 days late equals 5.00 fine.

### Slide 12: Dashboard, Notifications, And Reports

Main points:

- Dashboard statistics.
- Member notifications.
- Report generation.
- CSV report files.

Presenter notes:

Explain how these features help library staff monitor activity and make decisions.

### Slide 13: Testing Result

Main points:

- Django system check passed.
- Migration check passed.
- 12 automated tests passed.
- Database integrity passed.

Presenter notes:

Mention that tests cover the 11 tables, relationships, borrowing, returning, fines, notifications, reports, and seed data.

### Slide 14: Problems And Solutions

Main points:

- Earlier design had too many tables.
- Borrow records used BookCopy.
- Notifications connected to wrong target.
- Reports table needed to be added.
- Fixed by rebuilding active schema around lecturer Data Dictionary.

Presenter notes:

Show that you can identify mistakes and correct them professionally.

### Slide 15: Conclusion And Future Improvements

Main points:

- System is complete for corrected 11-table requirements.
- Main workflows work.
- Documentation and tests are included.
- Future: barcode, email reminders, PDF/Excel reports, API, backup tools.

Presenter notes:

End confidently and thank the lecturer.

## 2. Demonstration Script

Recommended demo length: 10 to 15 minutes.

### Minute 0-1: Introduction

Say:

"Good morning/afternoon. My project is the Enterprise Library Management System developed using Python Django. The final version follows the lecturer's corrected 11-table Data Dictionary."

Show:

- Title slide
- Project folder

### Minute 1-2: Login

Show:

- Login page
- Login using `sample_admin`

Say:

"The system uses Django authentication with a custom users table. Different users can access different pages depending on role and staff status."

### Minute 2-3: Dashboard

Show:

- Dashboard statistics

Say:

"The dashboard summarizes books, members, borrowed books, overdue records, fines, and recent borrow activity."

### Minute 3-5: Master Data

Show:

- Roles
- Users
- Categories
- Authors
- Publishers
- Books
- Members

Say:

"Library staff can manage all master data. Books are connected to categories, authors, and publishers. Members are connected to user accounts."

### Minute 5-7: Borrow Book

Show:

- Borrowing page
- Issue book form
- Select member and book

Say:

"When a book is borrowed, the system creates a borrow record. It stores the member, book, issue date, due date, and the staff user who issued it."

Show:

- Book availability decreases

### Minute 7-9: Return Book And Fine

Show:

- Return form
- Return late book
- Fine list

Say:

"When the book is returned late, the system calculates the fine automatically. The fine is connected to the borrow record and member."

### Minute 9-10: Notifications

Show:

- Notifications page

Say:

"Notifications are stored for members. Late returns can create fine notifications."

### Minute 10-11: Reports

Show:

- Reports page
- Generate report

Say:

"Reports are stored in the reports table and linked to the user who generated them."

### Minute 11-12: Database

Show:

- Data Dictionary documentation
- Models or ER diagram

Say:

"The active schema contains exactly the 11 required application tables."

### Minute 12-13: Testing

Show:

- Test result screenshot or terminal

Say:

"The system passed 12 automated tests, including schema verification, borrowing, returning, fine calculation, notification, report generation, and seed data."

### Minute 13-15: Conclusion

Say:

"In conclusion, the system meets the corrected project requirements, follows the Data Dictionary, and provides the core library workflows. Future improvements can include barcode, email reminders, PDF reports, Excel export, and API endpoints."

## 3. Common Lecturer Questions With Answers

### Q1. Why did you use Django?

Answer:

Django provides built-in authentication, admin, ORM, forms, templates, validation, and testing. These features make it suitable for a database-driven library system.

### Q2. Why does the final system have only 11 application tables?

Answer:

Because the lecturer's corrected Data Dictionary required exactly 11 application tables. I adjusted the final active schema to match those requirements exactly.

### Q3. Why does BorrowRecord connect to Book instead of BookCopy?

Answer:

The lecturer specifically required `borrow_records.book_id` to reference `books`. Therefore the final corrected system uses Book directly and does not use BookCopy in borrow records.

### Q4. How are fines calculated?

Answer:

The system counts how many days the return date is after the due date and multiplies that number by the fine rate of 1.00 per day.

### Q5. How do you know the database relationships are correct?

Answer:

The system has automated tests that verify the table names, primary keys, and foreign key relationships. I also ran database integrity checks and migration checks.

### Q6. Are reservations implemented?

Answer:

No, reservations are documented as a future improvement because the corrected lecturer Data Dictionary does not include a reservations table.

### Q7. Does the system have an API?

Answer:

The corrected final system does not expose active API endpoints. The final focus is the 11-table Django web application. API endpoints can be added later using the corrected models.

### Q8. What is the strongest part of your project?

Answer:

The strongest part is that the final implementation follows the corrected Data Dictionary exactly and includes working borrowing, returning, fine calculation, notifications, reports, sample data, and tests.

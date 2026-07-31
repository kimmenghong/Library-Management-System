# Enterprise Library Management System

## Final University Project Report

### Cover Page

**Project Title:** Enterprise Library Management System  
**Project Type:** University Final Project  
**Backend:** Python Django  
**Database:** Supabase PostgreSQL  
**Authentication:** Supabase Auth with Django role-based access control  
**Frontend:** HTML, CSS, Bootstrap 5, JavaScript  
**Deployment Platform:** Render  
**Version:** 1.0.0  

**Student Name:** [Insert Student Name]  
**Student ID:** [Insert Student ID]  
**Course / Program:** [Insert Course or Program Name]  
**Department:** [Insert Department Name]  
**University:** [Insert University Name]  
**Lecturer / Supervisor:** [Insert Lecturer Name]  
**Academic Year:** [Insert Academic Year]  
**Submission Date:** [Insert Submission Date]  

---

## Approval Page

This final project report entitled **Enterprise Library Management System** has been prepared and submitted by:

**Student Name:** [Insert Student Name]  
**Student ID:** [Insert Student ID]

This project is submitted in partial fulfillment of the requirements for the university final project.

**Supervisor / Lecturer Approval**

Name: _______________________________  
Signature: ____________________________  
Date: _________________________________

**Department Approval**

Name: _______________________________  
Signature: ____________________________  
Date: _________________________________

---

## Declaration

I declare that this project report, entitled **Enterprise Library Management System**, is my own work and has been prepared for academic submission. The system was developed using Django, Supabase PostgreSQL, Supabase Auth, Bootstrap 5, and Render deployment. All source code, documentation, screenshots, and testing evidence were prepared for the purpose of this final project.

I also declare that no real production passwords, secret keys, database credentials, or private access tokens are included in this report. All credentials shown in the documentation are placeholders or demonstration-only values.

Student Name: _________________________  
Signature: ____________________________  
Date: _________________________________

---

## Acknowledgement

First, I would like to thank my lecturer and supervisor for the guidance, advice, and feedback provided during the development of this project. Their comments helped me improve the system structure, database design, testing process, and final documentation.

I would also like to thank my university, classmates, and family for their support throughout the project period. Their encouragement helped me complete the research, development, testing, deployment, and report preparation.

Finally, I am grateful for the open-source technologies used in this project, including Django, PostgreSQL, Supabase, Bootstrap, Gunicorn, WhiteNoise, and Render. These tools made it possible to build a professional web-based Library Management System suitable for academic demonstration and portfolio presentation.

---

## Abstract

The **Enterprise Library Management System** is a web-based application developed to manage university library operations more efficiently. The system replaces manual record keeping with a computerized platform for managing books, members, users, borrowing, returning, fines, notifications, and reports.

The backend was developed using Python Django. Supabase PostgreSQL was used as the hosted production database, while Supabase Auth was integrated for email and password authentication. Django keeps the lecturer-required `users` table for user profiles, roles, and authorization. The frontend uses Bootstrap 5 to provide a responsive and professional user interface. The system is deployed online using Render.

The project follows the lecturer's required 11-table Data Dictionary exactly for the main business database structure. These tables are `roles`, `users`, `categories`, `authors`, `publishers`, `books`, `members`, `borrow_records`, `fines`, `notifications`, and `reports`. The application supports role-based access control, book catalog management, member management, borrowing and returning workflows, automatic fine calculation, notification history, CSV report generation, search and filtering, and dashboard statistics.

Testing was completed using Django's testing framework. The final test suite includes model, workflow, authentication, role-permission, report, notification, and seed-data tests. The system passed the final test suite with 30 tests. The final result is a complete, deployable, and presentation-ready Library Management System suitable for university final project submission.

---

## Table of Contents

1. Chapter 1: Introduction  
2. Chapter 2: Literature Review  
3. Chapter 3: System Analysis  
4. Chapter 4: System Design  
5. Chapter 5: System Implementation  
6. Chapter 6: Testing and Results  
7. Chapter 7: Deployment  
8. Chapter 8: System Screenshots  
9. Chapter 9: Discussion  
10. Chapter 10: Conclusion and Recommendations  
11. References  
12. Appendices  

---

## List of Figures

Figure 1: Login page with library image  
Figure 2: Registration page  
Figure 3: Dashboard statistics  
Figure 4: User and role management  
Figure 5: Category management  
Figure 6: Author management  
Figure 7: Publisher management  
Figure 8: Book management  
Figure 9: Member management  
Figure 10: Borrow book process  
Figure 11: Return book process  
Figure 12: Overdue record  
Figure 13: Fine calculation  
Figure 14: Notification page  
Figure 15: Reports page  
Figure 16: Search and filtering  
Figure 17: Supabase Auth users  
Figure 18: Supabase database tables  
Figure 19: Django test results  
Figure 20: Render deployed website  

---

## List of Tables

Table 1: Functional Requirements  
Table 2: Non-Functional Requirements  
Table 3: User Roles  
Table 4: Technology Stack  
Table 5: Lecturer's 11-Table Data Dictionary  
Table 6: Database Foreign Key Relationships  
Table 7: Implementation Summary  
Table 8: Test Result Summary  
Table 9: Errors Found and Fixed  
Table 10: Production Environment Variables  
Table 11: Final Submission Checklist  

---

# Chapter 1: Introduction

## 1.1 Background

Libraries are important academic resources for universities. They provide books, references, research materials, and learning support for students, teachers, and staff. In many institutions, library activities are still recorded manually or with simple spreadsheet files. This can create problems such as duplicated records, lost borrowing history, inaccurate stock quantity, slow searching, and difficulty tracking overdue books.

The Enterprise Library Management System was developed to solve these problems by providing a centralized web-based system. The system helps librarians manage books, members, borrowing records, fines, notifications, and reports. It also gives administrators better control over users and roles.

## 1.2 Problem Statement

Manual library management can create several challenges:

- Book information may be difficult to search and update.
- Borrowing and returning records may be lost or duplicated.
- Fine calculation may be incorrect when done manually.
- Library staff may have difficulty knowing which books are available, borrowed, lost, damaged, or under repair.
- Reports may take a long time to prepare.
- User access may not be properly controlled.
- Paper-based records can be damaged, misplaced, or hard to maintain.

This project provides a computerized system to improve accuracy, reduce manual work, and support library management decisions.

## 1.3 Project Objectives

The main objectives of this project are:

1. To manage book information accurately and systematically.
2. To manage library members, including students, teachers, staff, and librarians.
3. To register new books and update book information.
4. To manage book borrowing and returning.
5. To track book status, including available, borrowed, lost, damaged, and under repair.
6. To search books by title, author, category, ISBN, and status.
7. To manage book categories, authors, and publishers.
8. To manage library stock using total quantity and available quantity.
9. To calculate fines automatically for late returns.
10. To store member notification history.
11. To generate reports for books, members, borrowing, and fines.
12. To improve data security using role-based access control.
13. To reduce paper-based work and manual recording errors.
14. To provide dashboard statistics for management decision-making.

## 1.4 Project Scope

The scope of this project includes:

- User and role management
- Member management
- Category, author, publisher, and book management
- Borrowing and returning workflow
- Overdue tracking
- Fine calculation and fine status
- Member notifications
- Report generation and report history
- Search and filtering
- Dashboard statistics
- Supabase Auth login and registration integration
- Supabase PostgreSQL database connection
- Render deployment

The system does not claim to include advanced commercial features such as RFID hardware integration, online payment gateway integration, mobile application publishing, or real-time SMS notification.

## 1.5 Project Significance

This project is significant because it improves the reliability and efficiency of university library operations. It provides a structured database, secure user access, automatic fine calculation, and faster information retrieval. It also helps library staff generate reports that support better decision-making.

For students, the system provides a clear demonstration of full-stack web application development using modern technologies. It also shows practical use of Django, PostgreSQL, Supabase Auth, role-based access control, testing, and deployment.

---

# Chapter 2: Literature Review

## 2.1 Library Management Systems

A Library Management System is software used to manage library resources and daily operations. Common functions include catalog management, member registration, borrowing, returning, fine tracking, and reporting. A computerized system allows librarians to access information quickly and reduces the risk of manual errors.

## 2.2 Manual Versus Computerized Systems

Manual systems depend on paper records or simple files. They are easy to start but become difficult to maintain as the library grows. Searching records, calculating fines, and preparing reports can take a long time.

Computerized systems use a database and application interface. They improve accuracy, speed, security, and reporting. They also make it easier to control user permissions and preserve historical records.

## 2.3 Django

Django is a Python web framework that supports rapid and secure web application development. It includes useful features such as models, views, forms, templates, authentication support, admin interface, middleware, and security protections. In this project, Django is used as the main backend framework.

## 2.4 PostgreSQL

PostgreSQL is a powerful relational database system. It supports primary keys, foreign keys, constraints, indexes, and transactions. These features are important for maintaining data integrity in a Library Management System. In this project, PostgreSQL is provided through Supabase.

## 2.5 Supabase

Supabase is a backend platform that provides hosted PostgreSQL, authentication, storage, and API services. This project uses Supabase PostgreSQL as the production database. Supabase makes it easier to deploy the database online and verify tables through the Supabase dashboard.

## 2.6 Supabase Auth

Supabase Auth provides email and password authentication. In this system, Supabase Auth handles login and registration authentication, while Django keeps the local `users` table for roles, profile information, and authorization. This approach preserves the lecturer's required Data Dictionary while using a modern external authentication service.

---

# Chapter 3: System Analysis

## 3.1 Current System Problems

The current manual or semi-manual library process has the following problems:

- Records can be duplicated or lost.
- Book availability is difficult to track.
- Borrowing history is hard to search.
- Fine calculation can be inconsistent.
- Reports require manual preparation.
- Staff permissions are not clearly controlled.
- It is difficult to prove database relationships and data integrity.

## 3.2 Proposed System

The proposed system is a Django web application connected to Supabase PostgreSQL. It uses Supabase Auth for email and password authentication and Django role-based access control for internal permissions. The system manages the full workflow from catalog setup to borrowing, returning, fine calculation, notifications, and reports.

## 3.3 Functional Requirements

**Table 1: Functional Requirements**

| No. | Requirement | Implementation Status |
| --- | --- | --- |
| 1 | Login and logout | Completed |
| 2 | Supabase Auth registration and login | Completed |
| 3 | Role-based access control | Completed |
| 4 | User and role management | Completed |
| 5 | Category management | Completed |
| 6 | Author management | Completed |
| 7 | Publisher management | Completed |
| 8 | Book management | Completed |
| 9 | Member management | Completed |
| 10 | Borrow book workflow | Completed |
| 11 | Return book workflow | Completed |
| 12 | Automatic fine calculation | Completed |
| 13 | Member notification history | Completed |
| 14 | Report generation | Completed as CSV reports |
| 15 | Dashboard statistics | Completed |
| 16 | Search and filtering | Completed |

## 3.4 Non-Functional Requirements

**Table 2: Non-Functional Requirements**

| Requirement | Description |
| --- | --- |
| Security | Uses environment variables, role-based access control, CSRF protection, and secure production settings. |
| Reliability | Uses relational database constraints and automated tests. |
| Usability | Provides Bootstrap 5 responsive pages and clear forms. |
| Maintainability | Uses Django app structure, forms, templates, services, and tests. |
| Performance | Uses indexed fields and query optimization such as `select_related`. |
| Deployability | Supports Render deployment with Gunicorn and WhiteNoise. |

## 3.5 User Roles

**Table 3: User Roles**

| Role | Main Access |
| --- | --- |
| Super Admin | Full system access and administration. |
| Admin | User, role, catalog, circulation, and report management. |
| Librarian | Catalog, circulation, notification, and report access. |
| Assistant Librarian | Catalog and circulation support access. |
| Student | Member-level access to book search and personal notifications. |
| Teacher | Member-level access to book search and personal notifications. |
| Staff | Member-level access depending on assigned role. |
| Guest / Visitor | Public access only where enabled, such as login and public-facing pages. |

## 3.6 Use-Case Explanation

The main use cases are:

1. Admin logs in and manages roles and users.
2. Librarian creates categories, authors, publishers, and books.
3. Librarian registers a member.
4. Librarian issues a book to a member.
5. System decreases available book quantity.
6. Member returns the book.
7. System records the receiving user and return date.
8. If the return is late, system calculates a fine.
9. System creates a notification for the member.
10. Admin or librarian generates a report.

---

# Chapter 4: System Design

## 4.1 System Architecture

The system uses a layered architecture:

- Presentation layer: Bootstrap 5 templates, CSS, and JavaScript.
- Application layer: Django views, forms, services, and role checks.
- Data access layer: Django ORM.
- Database layer: Supabase PostgreSQL.
- Authentication service: Supabase Auth.
- Deployment layer: Render, Gunicorn, and WhiteNoise.

**Table 4: Technology Stack**

| Layer | Technology |
| --- | --- |
| Backend | Python Django |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth and Django session login |
| Authorization | Django role-based access control |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Static Files | WhiteNoise |
| Reports | CSV report generation |
| Deployment | Render and Gunicorn |
| Testing | Django test framework |

## 4.2 Database Design

The lecturer required exactly 11 main business tables. The project follows these table names and primary key names using Django model `db_table` and explicit primary key fields.

**Table 5: Lecturer's 11-Table Data Dictionary**

| No. | Table Name | Primary Key | Main Purpose |
| --- | --- | --- | --- |
| 1 | `roles` | `role_id` | Stores system roles for access control. |
| 2 | `users` | `user_id` | Stores system users, profile data, and assigned role. |
| 3 | `categories` | `category_id` | Stores book categories/classifications. |
| 4 | `authors` | `author_id` | Stores book author records. |
| 5 | `publishers` | `publisher_id` | Stores publisher information. |
| 6 | `books` | `book_id` | Stores book catalog and stock information. |
| 7 | `members` | `member_id` | Stores library member profiles. |
| 8 | `borrow_records` | `borrow_id` | Stores borrowing and returning transactions. |
| 9 | `fines` | `fine_id` | Stores fine amount, payment status, and balance. |
| 10 | `notifications` | `notification_id` | Stores member notification history. |
| 11 | `reports` | `report_id` | Stores generated report metadata and file path. |

## 4.3 ERD Explanation

The ERD is based on one-to-many and one-to-one relationships:

- One role can have many users.
- One user can have one member profile.
- One category can have many books.
- One author can have many books.
- One publisher can have many books.
- One member can have many borrow records.
- One book can appear in many borrow records.
- One borrow record can have fine records.
- One member can have many fines.
- One member can have many notifications.
- One user can generate many reports.
- Borrow records connect to users through `issued_by` and `received_by`.

**Table 6: Database Foreign Key Relationships**

| Child Table | Foreign Key | Parent Table | Purpose |
| --- | --- | --- | --- |
| `users` | `role_id` | `roles` | Assigns role to user. |
| `books` | `category_id` | `categories` | Assigns category to book. |
| `books` | `author_id` | `authors` | Assigns author to book. |
| `books` | `publisher_id` | `publishers` | Assigns publisher to book. |
| `members` | `user_id` | `users` | Links member profile to user. |
| `borrow_records` | `member_id` | `members` | Links borrow transaction to member. |
| `borrow_records` | `book_id` | `books` | Links borrow transaction to book. |
| `borrow_records` | `issued_by` | `users` | Stores staff user who issued the book. |
| `borrow_records` | `received_by` | `users` | Stores staff user who received the returned book. |
| `fines` | `borrow_id` | `borrow_records` | Links fine to borrowing transaction. |
| `fines` | `member_id` | `members` | Links fine to member. |
| `notifications` | `member_id` | `members` | Links notification to member. |
| `reports` | `generated_by` | `users` | Stores user who generated the report. |

## 4.4 Primary Keys

Each required table uses the lecturer-specified primary key:

`role_id`, `user_id`, `category_id`, `author_id`, `publisher_id`, `book_id`, `member_id`, `borrow_id`, `fine_id`, `notification_id`, and `report_id`.

## 4.5 Foreign Keys

Foreign keys protect data integrity. For example, a borrow record cannot be created without a valid member, book, and issuing user. A fine must connect to both a borrow record and a member. A notification must connect to a member, and a report must connect to the user who generated it.

## 4.6 User-Interface Design

The user interface uses Bootstrap 5 with responsive pages, cards, forms, tables, badges, navigation, and alert messages. The login page includes a professional library image. After login, users see a dashboard, sidebar navigation, and role-aware menu items. Tables support clear scanning, filtering, and action buttons.

---

# Chapter 5: System Implementation

## 5.1 Project Folder Structure

```text
Library Management System/
|-- apps/
|   `-- library/
|       |-- management/commands/
|       |-- migrations/
|       |-- services/
|       |-- admin.py
|       |-- apps.py
|       |-- forms.py
|       |-- models.py
|       |-- signals.py
|       |-- tests.py
|       |-- urls.py
|       `-- views.py
|-- config/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- templates/
|   `-- library/
|-- static/
|   |-- css/
|   |-- images/
|   `-- js/
|-- media/
|-- final_handover_package/
|-- requirements.txt
|-- .env.example
|-- Procfile
|-- build.sh
|-- render.yaml
`-- manage.py
```

## 5.2 Django Apps

The active corrected implementation uses the `apps.library` Django app. This app contains the required models, admin configuration, forms, views, URLs, templates, services, tests, seed command, and report generation logic. Older phase artifacts are not part of the active installed application.

## 5.3 Supabase Database Connection

The system uses Supabase PostgreSQL through environment variables. The database connection is configured in Django settings without hard-coding credentials. SSL mode is required for the production Supabase connection.

## 5.4 Supabase Authentication

Supabase Auth handles email and password authentication. Django still keeps the local `users` table because the lecturer's Data Dictionary requires it. After successful Supabase login, the system finds or syncs the user email with the Django `users` table and applies role-based access control.

## 5.5 Role-Based Access Control

Role-based access control is implemented through the `roles` and `users` tables. Users have role-based permissions such as managing users, managing catalog data, managing circulation, and generating reports. Inactive users and users without roles are blocked from login or management access.

## 5.6 Book Management

Book management includes category, author, publisher, and book records. Each book stores ISBN, title, edition, publication year, quantity, available quantity, shelf location, and status. The system validates that available quantity cannot exceed total quantity.

## 5.7 Member Management

Member management stores member code, member type, department, phone, address, registration date, and status. Member profiles are linked to system users through the `members.user_id` relationship.

## 5.8 Borrowing and Returning

Borrowing records connect a member, a book, the issuing user, and optionally the receiving user. When a book is issued, the available quantity is reduced. When a book is returned, the return date and receiving user are recorded, and the available quantity is increased.

## 5.9 Fine Calculation

The system calculates fines when a book is returned after the due date. The fine amount is based on the number of overdue days and the configured fine rate. Fine records store amount, paid amount, balance, status, and paid date.

## 5.10 Notifications

Notifications are linked to members. The system can store due-date, overdue, fine, and general notification messages. Members can view their own notification history.

## 5.11 Reports

The report module creates report records and stores generated report files. The implemented report format is CSV. Reports are linked to the user who generated them through `reports.generated_by`.

**Table 7: Implementation Summary**

| Module | Main Files | Status |
| --- | --- | --- |
| Authentication | `views.py`, `forms.py`, `services/supabase_auth.py` | Completed |
| Role and user management | `models.py`, `forms.py`, `views.py`, `admin.py` | Completed |
| Catalog management | `Book`, `Category`, `Author`, `Publisher` models | Completed |
| Member management | `Member` model and CRUD views | Completed |
| Borrowing and returning | `BorrowRecord` model and workflow views | Completed |
| Fine calculation | `Fine` model and return workflow | Completed |
| Notifications | `Notification` model and pages | Completed |
| Reports | `Report` model and CSV generation | Completed |
| Deployment | Render files and environment configuration | Completed |
| Testing | `apps/library/tests.py` | Completed |

---

# Chapter 6: Testing and Results

## 6.1 Unit Testing

Unit tests were written using Django's test framework. The tests check model behavior, table names, primary keys, relationships, validation, and fine calculation.

## 6.2 Integration Testing

Integration tests verify that pages render correctly and workflows operate together. These include borrowing, returning, generating fines, creating notifications, and generating reports.

## 6.3 Authentication Testing

Authentication tests verify login, registration, logout, Supabase Auth service calls, inactive user blocking, user-role validation, and local user synchronization.

## 6.4 Role-Permission Testing

Role tests verify that users can only access pages permitted by their role. For example, a student can view allowed pages but cannot manage users. A librarian can manage library operations but cannot manage users unless assigned the correct role.

## 6.5 Database Testing

Database tests verify that all 11 required tables exist with the correct table names and primary key names. Tests also confirm required relationships, such as `borrow_records.book_id`, `borrow_records.issued_by`, `borrow_records.received_by`, `notifications.member_id`, and `reports.generated_by`.

## 6.6 Test-Result Table

**Table 8: Test Result Summary**

| Test Area | Description | Result |
| --- | --- | --- |
| Data Dictionary | Checks 11 table names and primary keys | Passed |
| Foreign Keys | Checks required relationships | Passed |
| Borrowing | Checks issue book workflow | Passed |
| Returning | Checks return workflow and receiver | Passed |
| Fine Calculation | Checks overdue fine amount | Passed |
| Notifications | Checks member notification visibility | Passed |
| Reports | Checks report generation and file creation | Passed |
| Supabase Auth | Checks service integration and login flow | Passed |
| Role Permissions | Checks access restrictions | Passed |
| Seed Data | Checks sample data creation and repeatability | Passed |

Final local test result: **30 tests passed**.

## 6.7 Errors Found and Fixed

**Table 9: Errors Found and Fixed**

| Issue | Fix Applied |
| --- | --- |
| Earlier schema contained extra assignment tables | Corrected active app to lecturer's 11 required business tables. |
| Borrow records previously referenced book copies in older design | Updated active schema to use `book_id` foreign key to `books`. |
| Borrow records needed issuing and receiving users | Added `issued_by` and `received_by` relationships to `users`. |
| Notifications needed member relationship | Ensured `notifications.member_id` references `members`. |
| Reports table was required | Added `reports` table with `generated_by` foreign key to `users`. |
| Overdue status mutation during page load was risky | Added explicit overdue sync command and effective status display. |
| Supabase session tokens should not be stored in Django session | Updated session handling to avoid storing access and refresh tokens. |
| Role checks needed tighter separation | Added role capability checks for users, catalog, circulation, and reports. |

---

# Chapter 7: Deployment

## 7.1 Render Deployment

The project is prepared for deployment on Render. Render runs the Django application using Gunicorn. Build commands install requirements, run deployment checks, and collect static files. The application connects to Supabase PostgreSQL through environment variables.

## 7.2 Environment Variables

No secret values are stored in source code. The production system uses environment variables.

**Table 10: Production Environment Variables**

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` or `DJANGO_SECRET_KEY` | Django secret key. |
| `DEBUG` or `DJANGO_DEBUG` | Production debug setting, normally `False`. |
| `ALLOWED_HOSTS` or `DJANGO_ALLOWED_HOSTS` | Allowed production hostnames. |
| `CSRF_TRUSTED_ORIGINS` | Trusted HTTPS origins. |
| `DATABASE_ENGINE` | Database type, set to PostgreSQL. |
| `DATABASE_NAME` | Supabase database name. |
| `DATABASE_USER` | Supabase database user. |
| `DATABASE_PASSWORD` | Supabase database password. |
| `DATABASE_HOST` | Supabase database host or pooler host. |
| `DATABASE_PORT` | PostgreSQL port. |
| `DATABASE_SSLMODE` | SSL mode, normally `require`. |
| `SUPABASE_URL` | Supabase project URL. |
| `SUPABASE_ANON_KEY` | Supabase anonymous public key. |

## 7.3 Production Configuration

Production configuration includes:

- `DEBUG=False`
- Secure allowed hosts
- CSRF trusted origins
- HTTPS security settings
- Secure cookies
- WhiteNoise static file handling
- Environment variables for all secrets
- SSL mode required for Supabase PostgreSQL

## 7.4 Supabase Production Connection

Supabase PostgreSQL stores the production data. The system uses SSL and environment variables for database credentials. The lecturer-required 11 business tables are verified through Django migrations and the Supabase dashboard.

## 7.5 Security Configuration

Security measures include:

- No hard-coded secret keys
- No database password in source code
- Supabase Auth for email/password authentication
- Django role-based access control
- CSRF protection
- Secure production cookies
- File upload validation for report files
- Avoiding storage of Supabase access and refresh tokens in Django session

---

# Chapter 8: System Screenshots

## 8.1 Screenshot Evidence

The following screenshot placeholders should be replaced with actual screenshots before final printing or PDF export.

[Insert Figure 1: Login Page Here]

**Figure 1: Login page with professional library image and Supabase-ready authentication form.**  
This proves authentication interface design, Bootstrap layout, and static image loading.

[Insert Figure 2: Registration Page Here]

**Figure 2: Registration page for creating a new user account through Supabase Auth and local user sync.**  
This proves user registration and authentication support.

[Insert Figure 3: Dashboard Here]

**Figure 3: Dashboard showing total books, members, borrowed records, overdue records, and fines.**  
This proves dashboard statistics and management decision support.

[Insert Figure 4: User and Role Management Here]

**Figure 4: User and role management page showing system users and assigned roles.**  
This proves role-based access control and user administration.

[Insert Figure 5: Category Management Here]

**Figure 5: Category management page for organizing book classifications.**  
This proves category management.

[Insert Figure 6: Author Management Here]

**Figure 6: Author management page for maintaining author records.**  
This proves author management.

[Insert Figure 7: Publisher Management Here]

**Figure 7: Publisher management page for maintaining publisher records.**  
This proves publisher management.

[Insert Figure 8: Book Management Here]

**Figure 8: Book management page showing ISBN, title, stock quantity, available quantity, and status.**  
This proves book management, stock quantity, and book status tracking.

[Insert Figure 9: Member Management Here]

**Figure 9: Member management page showing student, teacher, staff, and librarian member profiles.**  
This proves member management.

[Insert Figure 10: Borrow Book Process Here]

**Figure 10: Borrow book workflow showing member, book, issue date, due date, and issuing user.**  
This proves the borrowing module and `issued_by` relationship.

[Insert Figure 11: Return Book Process Here]

**Figure 11: Return book workflow showing return date and receiving user.**  
This proves the returning module and `received_by` relationship.

[Insert Figure 12: Overdue Record Here]

**Figure 12: Overdue borrowing record showing due date tracking.**  
This proves overdue monitoring.

[Insert Figure 13: Fine Calculation Here]

**Figure 13: Fine page showing automatic late-return fine amount and balance.**  
This proves fine calculation.

[Insert Figure 14: Notification Page Here]

**Figure 14: Notification page showing member notification history.**  
This proves due-date, overdue, fine, and general notification support.

[Insert Figure 15: Reports Page Here]

**Figure 15: Reports page showing generated report records and generated-by user information.**  
This proves report generation and report history.

[Insert Figure 16: Search and Filtering Here]

**Figure 16: Search and filtering results for books by title, ISBN, author, category, or status.**  
This proves search and filter functionality.

[Insert Figure 17: Supabase Auth Users Here]

**Figure 17: Supabase Auth user list showing external email/password authentication setup.**  
This proves Supabase Auth integration. Sensitive values must be hidden.

[Insert Figure 18: Supabase Database Tables Here]

**Figure 18: Supabase PostgreSQL dashboard showing the 11 lecturer-required business tables.**  
This proves Data Dictionary compliance.

[Insert Figure 19: Django Test Results Here]

**Figure 19: Django test result showing the final test suite passing.**  
This proves testing and quality assurance.

[Insert Figure 20: Render Deployed Website Here]

**Figure 20: Render deployment evidence showing the online Library Management System.**  
This proves deployment and online access.

---

# Chapter 9: Discussion

## 9.1 Project Strengths

The main strengths of this project are:

- It follows the lecturer's required 11-table Data Dictionary.
- It uses Django best practices with models, forms, views, templates, admin, and tests.
- It integrates Supabase PostgreSQL for hosted production data.
- It uses Supabase Auth while preserving the required local `users` table.
- It supports role-based access control.
- It includes core library workflows: catalog, members, borrowing, returning, fines, notifications, and reports.
- It includes automated tests and sample data.
- It is prepared for online deployment using Render.
- It includes documentation, screenshot evidence, and handover materials.

## 9.2 Project Limitations

The project has the following limitations:

- Reports are implemented as CSV files, not advanced PDF or Excel dashboards.
- Online payment integration for fines is not included.
- SMS notification is not included.
- Hardware barcode scanner or RFID integration is not included.
- The system is web-based and does not include a separate native mobile application.
- Some advanced analytics are limited to dashboard summaries and reports.

## 9.3 Challenges and Solutions

One major challenge was keeping the system aligned with the lecturer's 11-table Data Dictionary while still using Django and Supabase Auth. This was solved by keeping the local `users` table for roles and profiles and using Supabase Auth only for email/password authentication.

Another challenge was maintaining correct relationships for borrowing and returning. This was solved by linking `borrow_records` directly to `books`, `members`, `issued_by`, and `received_by`.

Fine calculation also required careful validation. This was solved by calculating overdue days from the due date and return date, then creating a fine record when necessary.

Deployment required secure environment configuration. This was solved using environment variables, SSL database configuration, Render deployment files, and secret-safe documentation.

---

# Chapter 10: Conclusion and Recommendations

## 10.1 Conclusion

The Enterprise Library Management System successfully provides a computerized solution for managing university library operations. It supports book management, member management, borrowing, returning, fine calculation, notifications, reports, authentication, role-based access control, testing, and online deployment.

The system follows the lecturer's required 11-table Data Dictionary and uses modern web technologies, including Django, Supabase PostgreSQL, Supabase Auth, Bootstrap 5, and Render. The final test suite passed successfully, and the project is suitable for university final project demonstration and portfolio presentation.

## 10.2 Recommendations

It is recommended that the system be used with prepared sample data during the lecturer demonstration. Screenshots should be inserted into Chapter 8 before submission. Secret keys, database passwords, and Supabase tokens must not be included in the final report or presentation.

## 10.3 Future Improvements

Future improvements may include:

- PDF and Excel report export.
- Email notification scheduling.
- Barcode or QR code scanning.
- Online fine payment integration.
- Advanced analytics dashboard.
- Mobile application interface.
- Cloud media storage.
- More detailed audit logging.
- Automated backup scheduling.

---

# References

1. Django Software Foundation. Django Web Framework Documentation.  
2. PostgreSQL Global Development Group. PostgreSQL Documentation.  
3. Supabase. Supabase PostgreSQL and Supabase Auth Documentation.  
4. Bootstrap Team. Bootstrap 5 Documentation.  
5. Render. Render Web Service Deployment Documentation.  
6. Python Software Foundation. Python Documentation.  

---

# Appendices

## Appendix A: Data Dictionary

The final active business schema contains exactly the following 11 lecturer-required tables:

1. `roles`
2. `users`
3. `categories`
4. `authors`
5. `publishers`
6. `books`
7. `members`
8. `borrow_records`
9. `fines`
10. `notifications`
11. `reports`

Framework tables created by Django, such as migrations, sessions, content types, and admin logs, are not part of the lecturer's business Data Dictionary.

## Appendix B: Test Cases

Main test cases include:

1. Verify all 11 table names.
2. Verify all 11 primary key names.
3. Verify `borrow_records.book_id` references `books`.
4. Verify `borrow_records.issued_by` references `users`.
5. Verify `borrow_records.received_by` references `users`.
6. Verify `notifications.member_id` references `members`.
7. Verify `reports.generated_by` references `users`.
8. Test borrowing process.
9. Test returning process.
10. Test fine calculation.
11. Test notification creation.
12. Test report generation.
13. Test seed data creation.
14. Test Supabase Auth service integration.
15. Test role-based access control.

## Appendix C: Installation Guide

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Appendix D: User Manual Summary

1. Open the deployed website or local server.
2. Login using a demo account.
3. Use the dashboard to view statistics.
4. Manage categories, authors, publishers, and books.
5. Manage library members.
6. Issue a book from the borrowing page.
7. Return a book from the borrow record page.
8. View fines after late returns.
9. View notifications.
10. Generate reports.
11. Logout after finishing.

## Appendix E: Sample Login Roles

Use demonstration-only accounts prepared by the seed-data command. Do not include real production passwords in the report.

| Role | Example Username | Password |
| --- | --- | --- |
| Admin | `sample_admin` | `[Demo password only - fill manually if allowed]` |
| Librarian | `sample_librarian` | `[Demo password only - fill manually if allowed]` |
| Student / Member | `sample_student` | `[Demo password only - fill manually if allowed]` |

## Appendix F: Deployment URL Placeholder

Production URL:

```text
[Insert Render Deployment URL Here]
```

Supabase Project:

```text
[Insert Supabase Project Reference or Safe Public URL Here]
```

Do not insert database passwords, Supabase service-role keys, access tokens, refresh tokens, or Django secret keys.

---

# Final Report Checklist

- [ ] Cover page details completed.
- [ ] Approval page signed.
- [ ] Declaration signed.
- [ ] Abstract reviewed.
- [ ] Table of contents page numbers updated in Microsoft Word.
- [ ] List of figures updated.
- [ ] List of tables updated.
- [ ] All 20 screenshots inserted in Chapter 8.
- [ ] Screenshot captions checked.
- [ ] Data Dictionary checked against the 11 required tables.
- [ ] Test result screenshot inserted.
- [ ] Deployment URL inserted.
- [ ] No secret keys or passwords exposed.
- [ ] Final report exported to PDF.

# Missing Information to Fill Manually

1. Student name.
2. Student ID.
3. Course or program name.
4. Department name.
5. University name.
6. Lecturer or supervisor name.
7. Academic year.
8. Submission date.
9. Approval signatures.
10. Declaration signature.
11. Actual Render deployment URL.
12. Final screenshots.
13. Page numbers in the Table of Contents.
14. Demo account passwords only if the lecturer requires them and they are demonstration-only.

# Recommended Report Filename

```text
Enterprise_Library_Management_System_Final_Report.docx
```

# Recommended PDF Filename

```text
Enterprise_Library_Management_System_Final_Report.pdf
```

# Final Submission Order

1. Final report PDF.
2. Final report Word document.
3. Source code folder or GitHub repository link.
4. Database documentation and ERD.
5. Screenshot evidence folder.
6. Testing documentation.
7. User manual and administrator manual.
8. Deployment guide.
9. Presentation slides.
10. Demo video or demo link.
11. README and requirements file.
12. Final lecturer submission checklist.

**Table 11: Final Submission Checklist**

| Item | Status |
| --- | --- |
| Source code prepared | Ready |
| Requirements file included | Ready |
| `.env.example` included | Ready |
| Real `.env` excluded | Ready |
| 11-table Data Dictionary documented | Ready |
| Supabase PostgreSQL documented | Ready |
| Supabase Auth documented | Ready |
| Render deployment documented | Ready |
| Test results documented | Ready |
| Screenshot placeholders included | Ready |
| Final screenshots still need insertion | Manual action required |
| Lecturer details still need insertion | Manual action required |

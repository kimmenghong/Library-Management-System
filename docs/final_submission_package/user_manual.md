# Complete User Manual

Project: Enterprise Library Management System  
Version: Corrected 11-table Django implementation

## 1. Introduction

The Enterprise Library Management System is a Django-based web application designed to manage the main operations of a university library. It supports user login, dashboard statistics, user management, member management, book management, borrowing, returning, fine tracking, notifications, and reports.

This manual explains how ordinary users and library staff can use the system. The final corrected implementation follows the lecturer's 11-table Data Dictionary exactly.

## 2. Installation

### 2.1 Requirements

Install these requirements before running the project:

- Python 3
- pip
- Virtual environment support
- SQLite for development
- Web browser such as Chrome, Edge, Firefox, or Safari

### 2.2 Installation Steps

Open a terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py seed_data
python3 manage.py runserver
```

Open the system in a browser:

```text
http://127.0.0.1:8000/
```

Open the Django Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## 3. Login

### 3.1 Sample Accounts

After running `python3 manage.py seed_data`, these accounts are available:

| Username | Password | Role |
| --- | --- | --- |
| `sample_admin` | `Library@123` | Super Admin |
| `sample_librarian` | `Library@123` | Librarian |
| `sample_assistant` | `Library@123` | Assistant Librarian |
| `sample_student` | `Library@123` | Student |
| `sample_teacher` | `Library@123` | Teacher |
| `sample_staff` | `Library@123` | Staff |

### 3.2 Login Steps

1. Open the login page.
2. Enter your username.
3. Enter your password.
4. Click the login button.
5. If the details are correct, the system opens the dashboard.
6. If the details are wrong, the system displays a login error.

### 3.3 Logout Steps

1. Click the logout option in the navigation menu.
2. The system logs out the current user.
3. The system redirects back to the login page.

## 4. Dashboard

The dashboard provides a quick summary of the library's current status.

### 4.1 Dashboard Statistics

The dashboard shows:

- Total books
- Total members
- Available books
- Borrowed books
- Overdue books
- Unpaid fines
- Recent borrowing records

### 4.2 Dashboard Usage

Library staff can use the dashboard to monitor daily library activity. Students, teachers, and staff members can use the dashboard to view their own borrowing-related information.

## 5. Managing Users

User management is available to authorized library staff.

### 5.1 User Information

Each user record includes:

- Role
- Username
- Email
- Full name
- Phone
- Address
- Active status
- Staff status

### 5.2 Add User

1. Log in as an administrator or librarian.
2. Open the Users page.
3. Click Add.
4. Enter user details.
5. Select a role.
6. Enter password information if required.
7. Save the user.

### 5.3 Edit User

1. Open the Users page.
2. Select the user to edit.
3. Update the required fields.
4. Save the changes.

### 5.4 Delete User

1. Open the Users page.
2. Select the delete action.
3. Confirm deletion.
4. If the user is referenced by protected records, deletion may be blocked to protect data integrity.

## 6. Managing Members

Members are library users who can borrow books and receive notifications.

### 6.1 Member Types

The system supports:

- Student
- Teacher
- Staff
- Librarian

### 6.2 Member Status

Member status can be:

- Active
- Suspended
- Expired

Only active members should borrow books.

### 6.3 Add Member

1. Log in as library staff.
2. Open the Members page.
3. Click Add.
4. Select the related user account.
5. Enter member code.
6. Select member type.
7. Enter department, phone, address, and registration date.
8. Save the member.

### 6.4 Edit Member

1. Open the Members page.
2. Choose a member.
3. Update the information.
4. Save the changes.

### 6.5 Delete Member

Member deletion may be blocked if the member has borrowing records, fines, or related protected data. This prevents loss of transaction history.

## 7. Managing Books

Book management is available to library staff.

### 7.1 Book Information

Each book includes:

- Category
- Author
- Publisher
- ISBN
- Title
- Edition
- Publication year
- Quantity
- Available quantity
- Shelf location
- Status

### 7.2 Book Status

Book status can be:

- Available
- Borrowed
- Lost
- Damaged
- Under repair

### 7.3 Add Book

1. Log in as a librarian or administrator.
2. Open the Books page.
3. Click Add Book.
4. Select category, author, and publisher.
5. Enter ISBN and title.
6. Enter edition and publication year.
7. Enter total quantity and available quantity.
8. Enter shelf location.
9. Select status.
10. Save the book.

### 7.4 Edit Book

1. Open the Books page.
2. Select a book.
3. Edit the required details.
4. Save the changes.

### 7.5 Delete Book

1. Open the Books page.
2. Select delete.
3. Confirm deletion.
4. If the book has borrowing history, deletion is blocked to protect records.

### 7.6 Search And Filter Books

Books can be searched or filtered by:

- Title
- ISBN
- Author
- Publisher
- Category
- Shelf location
- Status

## 8. Borrowing Books

Borrowing is handled through the `borrow_records` table.

### 8.1 Borrowing Rules

- Only active members should borrow books.
- The selected book must have available quantity greater than zero.
- The selected book must have status Available.
- The system records the logged-in staff user as `issued_by`.
- The system reduces the book's available quantity after borrowing.

### 8.2 Borrow Book Steps

1. Log in as library staff.
2. Open the Borrowing page.
3. Click Issue Book.
4. Select the member.
5. Select the book.
6. Enter borrow date.
7. Enter due date.
8. Save the borrow record.

### 8.3 Borrowing Result

After saving:

- A new borrow record is created.
- The book's available quantity decreases by one.
- If available quantity becomes zero, the book status changes to Borrowed.
- The transaction records the staff user who issued the book.

## 9. Returning Books

Returning updates the original borrow record.

### 9.1 Return Rules

- Only active borrowed or overdue records can be returned.
- Return date cannot be earlier than borrow date.
- The logged-in staff user is recorded as `received_by`.
- The book's available quantity increases after return.
- Late returns generate fines.

### 9.2 Return Book Steps

1. Log in as library staff.
2. Open the Borrowing page.
3. Find the active borrow record.
4. Click Return.
5. Enter the return date.
6. Save the return.

### 9.3 Return Result

After saving:

- Borrow status changes to Returned.
- Return date is saved.
- Receiving staff user is saved.
- Book available quantity increases.
- Book status becomes Available.
- If returned late, a fine and notification are created.

## 10. Reservations

The corrected lecturer Data Dictionary does not include a `reservations` table. Therefore, the final active 11-table system does not implement a reservation module.

### 10.1 Current Handling

If a book is unavailable, library staff can:

- Inform the member manually.
- Check the Borrowing page for active records.
- Contact the current borrower if needed.
- Use notifications for general member messages.

### 10.2 Future Improvement

A reservation module can be added later by introducing a new `reservations` table and related workflow. It was not included in the corrected final submission because the lecturer required only 11 tables.

## 11. Fine Management

Fine management is used for late returned books.

### 11.1 Fine Calculation

The implemented fine rate is:

```text
1.00 per overdue day
```

Example:

```text
5 days late x 1.00 = 5.00 fine
```

### 11.2 View Fines

1. Log in.
2. Open the Fines page.
3. Staff can see all fines.
4. Members can see their own fines.

### 11.3 Pay Fine

1. Log in as library staff.
2. Open the Fines page.
3. Select a fine.
4. Click Pay.
5. Enter payment amount.
6. Save payment.

### 11.4 Fine Status

Fine status can be:

- Unpaid
- Partially paid
- Paid
- Waived

## 12. Notifications

Notifications are connected to members.

### 12.1 Notification Types

- Due date
- Overdue
- Fine
- General

### 12.2 View Notifications

1. Log in.
2. Open the Notifications page.
3. Staff can view all notifications.
4. Members can view their own notifications.

### 12.3 Create Notification

1. Log in as library staff.
2. Open Notifications.
3. Click Add Notification.
4. Select member.
5. Enter title and message.
6. Select notification type.
7. Save.

### 12.4 Mark Notification As Read

1. Open Notifications.
2. Choose the notification.
3. Mark it as read if the action is available.

## 13. Reports

Reports store generated report history and connect each report to the user who generated it.

### 13.1 Report Types

- Books
- Members
- Borrowing
- Fines

### 13.2 Generate Report

1. Log in as library staff.
2. Open Reports.
3. Click Generate Report.
4. Select report type.
5. Save.

### 13.3 Report Result

The system:

- Creates a report record.
- Records the logged-in user as `generated_by`.
- Generates a CSV report file when no file is uploaded manually.

## 14. Troubleshooting

### 14.1 Cannot Log In

Possible causes:

- Wrong username.
- Wrong password.
- User account is inactive.

Solution:

- Confirm login details.
- Ask administrator to check the user account.

### 14.2 Page Shows Permission Error Or Redirect

Possible causes:

- User is not library staff.
- User role does not allow access.

Solution:

- Log in using an administrator or librarian account.
- Ask administrator to update the user's role or staff status.

### 14.3 Book Cannot Be Borrowed

Possible causes:

- Book available quantity is zero.
- Book status is not Available.
- Member is not Active.

Solution:

- Update book stock.
- Update book status.
- Check member status.

### 14.4 Book Cannot Be Deleted

Possible cause:

- Book is referenced by borrow records.

Solution:

- Keep the book record for history.
- Change book status instead of deleting.

### 14.5 Migration Error

Solution:

```bash
python3 manage.py makemigrations --check --dry-run
python3 manage.py migrate
```

### 14.6 Static Files Not Loading

Solution:

```bash
python3 manage.py collectstatic
```

For development, confirm `static/` exists and the server is running with `DEBUG=True`.

### 14.7 Sample Data Missing

Solution:

```bash
python3 manage.py seed_data
```

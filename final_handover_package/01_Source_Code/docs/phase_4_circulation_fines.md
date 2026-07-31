# Phase 4: Circulation, Reservations, Fines, and Payments

## Completed Modules

1. Borrowing Module
2. Returning Module
3. Renewal Module
4. Reservation Module
5. Fine Management Module
6. Payment History Module

## Workflow Rules

- Only active members can borrow or reserve books.
- Members with unpaid fines cannot borrow new books.
- Borrowing limits are controlled by `BorrowingPolicy`.
- Only available book copies can be issued.
- Active borrow records can be returned or renewed.
- Overdue books cannot be renewed.
- Late returns automatically create a fine based on `fine_per_day`.
- Returning a book automatically updates the book copy status.

## Status Updates

- Borrowing a copy changes the copy status to `borrowed`.
- Returning in good condition changes the copy status to `available`.
- Returning as damaged, lost, or under repair changes the copy status accordingly.
- Parent book status is synchronized from its copies.

## Payment History

Each payment is stored separately and linked to a fine. The fine automatically updates:

- Unpaid
- Partially paid
- Paid
- Waived

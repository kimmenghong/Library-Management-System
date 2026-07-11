# Phase 5: Notifications, Email Reminders, and Book Status Tracking

## Completed Modules

1. Notification Module
2. Email Reminder Module
3. Book Status Tracking Module
4. Lost Book Module
5. Damaged Book Module
6. Repair Book Module

## Notification Features

- Member notification history
- Manual notification creation
- Due-date reminders
- Overdue book reminders
- Email reminder logs
- Read/unread tracking

## Status Tracking Features

- Every tracked book-copy status change is recorded in `BookStatusLog`.
- Lost book records update the copy status to `lost`.
- Damaged book records update the copy status to `damaged`.
- Repair records update the copy status to `under_repair`.
- Completing a repair updates the copy status back to `available`.

## Circulation Integration

Borrowing and returning now create status logs. Returning a book as lost, damaged, or under repair automatically creates the matching tracking record.

## Email Backend

The project still uses Django's console email backend for development, so generated email reminders are printed to the development server console.

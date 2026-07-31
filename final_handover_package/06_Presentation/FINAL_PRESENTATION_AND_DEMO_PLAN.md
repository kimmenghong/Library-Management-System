# Final Presentation and Demonstration Plan

## 15-Slide Presentation Structure

1. Project title and student information
2. Problem statement
3. Project objectives
4. Technology stack
5. System architecture
6. Lecturer 11-table database design
7. Authentication and role-based access
8. Book and member management
9. Borrowing and returning workflow
10. Fine calculation and notifications
11. Reports and dashboard analytics
12. Supabase PostgreSQL and Supabase Auth integration
13. Testing and validation result
14. Limitations and future improvements
15. Conclusion and live demonstration transition

## Speaker Notes

Keep the explanation simple and practical:

- Explain what problem the system solves.
- Show that the database follows the required 11 tables.
- Explain how Supabase Auth and Django roles work together.
- Demonstrate the real workflow instead of only discussing features.
- Mention testing, deployment, and security.

## 10-15 Minute Demonstration Script

1. Open the deployed Render URL.
2. Show the public homepage and login page with the library image.
3. Login using a prepared demo account.
4. Show dashboard statistics.
5. Open books and demonstrate search/filtering.
6. Add or view category, author, publisher, and book records.
7. Open members and show member details.
8. Borrow a book for a member.
9. Return the book.
10. Show fine calculation if return is late.
11. Show notifications.
12. Generate or view reports.
13. Show role-based access control using a lower-privilege account.
14. Open Supabase and show the 11 business tables.
15. Close with limitations and future improvements.

## Demo Workflow

- Public page
- Supabase Auth login
- Dashboard
- Book management
- Member management
- Borrowing
- Returning
- Fine management
- Notifications
- Reports
- Supabase table verification

## Common Lecturer Questions

1. Why did you use Django?
   - Django provides authentication, admin tools, ORM, security protections, and fast development.
2. Why Supabase PostgreSQL?
   - It provides managed PostgreSQL, dashboard tools, hosted database access, and Supabase Auth.
3. How many required tables are used?
   - The final business schema uses exactly 11 lecturer-required tables.
4. Does BorrowRecord use BookCopy?
   - No. It uses `book_id` directly to the `books` table as required.
5. How does authentication work?
   - Supabase Auth verifies email/password. Django `users` table stores role, profile, and status.
6. How are permissions controlled?
   - Django checks the local user role and active status.
7. How are fines calculated?
   - The system compares return date with due date and creates fine records for late returns.
8. How are notifications linked?
   - Notifications are linked to `members` through `member_id`.
9. How are reports linked?
   - Reports are linked to the generating user through `generated_by`.
10. What is the main limitation?
   - The current version focuses on the required 11-table academic scope and can later expand to advanced modules.

## Backup Screenshots List

- Homepage/login page
- Dashboard
- Book list
- Add/edit book form
- Member list
- Borrow record form
- Return workflow
- Fine page
- Notification page
- Report page
- Supabase 11-table list
- Render deployment page

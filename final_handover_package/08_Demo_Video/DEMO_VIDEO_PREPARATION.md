# Demo Video Preparation

## Recording Checklist

- Use the deployed Render URL.
- Use demo accounts only.
- Hide browser password manager popups.
- Do not show `.env`, Supabase keys, or database passwords.
- Keep the video between 10 and 15 minutes.
- Record in 1080p if possible.
- Speak slowly and clearly.

## Screen Recording Sequence

1. Open the deployed homepage.
2. Show the login page and library image.
3. Login with Supabase Auth.
4. Show dashboard statistics.
5. Show book management.
6. Show member management.
7. Borrow a book.
8. Return a book.
9. Show automatic fine calculation.
10. Show notifications.
11. Show reports.
12. Show Supabase database verification.
13. Explain security and role access.
14. End with conclusion and future improvements.

## Voice-Over Script

Hello, this is my Enterprise Library Management System. The system was developed with Django, Bootstrap 5, Supabase PostgreSQL, Supabase Auth, and Render deployment.

The system follows the lecturer's required 11-table Data Dictionary. Supabase Auth is used for email and password authentication, while the Django `users` table stores role, status, and profile information.

First, I will log in using a demo account. After login, the dashboard shows key statistics such as books, members, borrowed books, fines, and reports.

Next, I will show book management, including categories, authors, publishers, and books. Then I will show member management and the borrowing process. When a book is borrowed, the system updates available quantity. When the book is returned late, the system calculates a fine.

The notification module stores messages for members, and the report module records generated reports with the user who created them.

Finally, I will show the Supabase PostgreSQL database and verify the 11 required tables. This confirms that the deployed Django system is saving data to the online database.

Thank you.

## Demo Account Safety

- Use only sample accounts.
- Do not reveal production admin passwords.
- If a password must be spoken, clearly say it is a demonstration-only password.

## Backup Plan

If the internet connection fails:

- Use prepared screenshots from `07_Screenshots`.
- Use a locally recorded demo video.
- Explain that the deployed system normally runs on Render with Supabase PostgreSQL.

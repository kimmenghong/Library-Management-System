# Final Screenshot and Evidence Package

Project: Enterprise Library Management System  
Stack: Django, Supabase PostgreSQL, Supabase Auth, Bootstrap 5, Render  
Database requirement: lecturer's final 11-table Data Dictionary

## Screenshot Folder Structure

```text
07_Screenshots/
├── 01_Public_Auth
├── 02_Core_System
├── 03_Circulation_Fines
├── 04_Reports_Search
├── 05_Supabase_Evidence
├── 06_Testing_Deployment
└── 99_Backup_Screenshots
```

## Screenshot Plan

| No. | Screenshot | Page to Open | Action to Perform | Sample Data to Display | File Name | Caption | Lecturer Requirement Proved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Login page with library image | `/login/` or deployed login URL | Open page before entering password | Library background image, logo, login form | `01_Public_Auth/01_login_page_library_image.png` | Login page with professional library branding and Supabase-ready authentication form. | Authentication module, Bootstrap UI, static image loading |
| 02 | Registration page | `/register/` | Open registration form, do not show password | Sample name: New Student Member, email field visible only | `01_Public_Auth/02_registration_page.png` | Registration page for creating a library user through Supabase Auth and local profile sync. | User registration, Supabase Auth, profile creation |
| 03 | Dashboard | `/` after login | Login as admin/librarian and open dashboard | Total books, members, borrowed, overdue, fines | `02_Core_System/03_dashboard_statistics.png` | Dashboard showing key library statistics and recent circulation activity. | Dashboard module, analytics, management decision support |
| 04 | User and role management | `/manage/users/` and `/manage/roles/` | Open users page, then roles page if needed | `sample_admin`, `sample_librarian`, roles list | `02_Core_System/04_user_role_management.png` | User and role management showing role-based system accounts. | User management, role-based access control |
| 05 | Category management | `/manage/categories/` | Open category list | Computer Science, Business, Engineering | `02_Core_System/05_category_management.png` | Category management page for organizing book classifications. | Category management, book classification |
| 06 | Author management | `/manage/authors/` | Open author list | Robert C. Martin, Andrew S. Tanenbaum | `02_Core_System/06_author_management.png` | Author management page for maintaining book author records. | Author management |
| 07 | Publisher management | `/manage/publishers/` | Open publisher list | Pearson Education, MIT Press, University Press | `02_Core_System/07_publisher_management.png` | Publisher management page for maintaining publisher records. | Publisher management |
| 08 | Book management | `/books/` | Open books list and show action buttons | Clean Code, ISBN, available quantity, status | `02_Core_System/08_book_management.png` | Book management page showing catalog records, ISBN, stock, and status. | Book management, stock quantity, book status |
| 09 | Member management | `/manage/members/` | Open member list | `STU-2026-001`, teacher/staff member rows | `02_Core_System/09_member_management.png` | Member management page showing student, teacher, and staff library members. | Member management |
| 10 | Borrow book process | `/borrowing/issue/` | Open issue form or show successful borrow record | Member `STU-2026-001`, book `Clean Code`, due date | `03_Circulation_Fines/10_borrow_book_process.png` | Borrowing workflow where a librarian issues a book to an active member. | Borrowing module, issued_by user, book/member relationship |
| 11 | Return book process | `/borrowing/<borrow_id>/return/` | Open return form or show returned record | Borrow ID, returned status, received_by user | `03_Circulation_Fines/11_return_book_process.png` | Return workflow recording return date and receiving staff user. | Returning module, received_by user, return validation |
| 12 | Overdue record | `/borrowing/?status=overdue` | Filter borrow records by overdue | Overdue badge, due date in past | `03_Circulation_Fines/12_overdue_record.png` | Overdue borrowing record showing due-date tracking. | Overdue tracking, borrowing history |
| 13 | Fine calculation | `/fines/` | Open fines page after late return | Fine amount, paid amount, balance, unpaid status | `03_Circulation_Fines/13_fine_calculation.png` | Fine page showing automatic late-return fine calculation and balance. | Fine management, late return calculation |
| 14 | Notification page | `/notifications/` | Open notification list | Due date, overdue, or fine notification | `03_Circulation_Fines/14_notification_page.png` | Member notification history showing due-date, overdue, and fine messages. | Notification module, member notification history |
| 15 | Reports page | `/reports/` | Open reports page or generate a CSV report | Books report, borrowing report, generated_by user | `04_Reports_Search/15_reports_page.png` | Reports page showing generated reports and analytics summary. | Report module, generated_by user, analytics |
| 16 | Search and filtering | `/books/?q=Clean` or use search field | Search by title/ISBN/author/category/status | Search term `Clean`, filtered book row | `04_Reports_Search/16_search_filtering.png` | Search and filtering results for books by title, ISBN, author, category, or status. | Search and filter objective |
| 17 | Supabase Auth users | Supabase Dashboard > Authentication > Users | Show user list, hide sensitive columns/details | Demo user emails only, no tokens | `05_Supabase_Evidence/17_supabase_auth_users.png` | Supabase Auth user list proving external email/password authentication setup. | Supabase Auth integration |
| 18 | Supabase database tables | Supabase Dashboard > Table Editor or SQL Editor | Show the 11 required table names | roles, users, categories, authors, publishers, books, members, borrow_records, fines, notifications, reports | `05_Supabase_Evidence/18_supabase_11_tables.png` | Supabase PostgreSQL database showing the lecturer-required 11 business tables. | Data Dictionary compliance |
| 19 | Django test results | Terminal | Run `python manage.py test` | `Ran 30 tests`, `OK` | `06_Testing_Deployment/19_django_test_results.png` | Django test suite passing successfully after final review fixes. | Testing evidence, quality assurance |
| 20 | Render deployed website | Render Dashboard and public website | Show deployed service or public URL homepage | Render service status, live site URL | `06_Testing_Deployment/20_render_deployed_website.png` | Render deployment evidence showing the online Library Management System. | Deployment, public online access |

## Correct Order in Final Report

Use this order:

1. Login page
2. Registration page
3. Dashboard
4. User and role management
5. Category management
6. Author management
7. Publisher management
8. Book management
9. Member management
10. Borrow book process
11. Return book process
12. Overdue record
13. Fine calculation
14. Notification page
15. Reports page
16. Search and filtering
17. Supabase Auth users
18. Supabase database tables
19. Django test results
20. Render deployed website

## Screenshot Checklist

- [ ] All 20 required screenshots captured.
- [ ] Screenshots use the suggested file names.
- [ ] Screenshots are placed in the correct folder.
- [ ] Browser zoom is between 90% and 100%.
- [ ] Main content is readable.
- [ ] No passwords or tokens are visible.
- [ ] No real private user/member data is visible.
- [ ] Captions are copied into the final report.
- [ ] Supabase evidence shows table names, not secret keys.
- [ ] Render evidence shows service status, not environment variables.
- [ ] Test screenshot clearly shows `OK`.

## Demo-Data Preparation Checklist

Before taking screenshots:

```bash
python manage.py migrate
python manage.py seed_data
python manage.py sync_overdue_records
python manage.py test
python manage.py runserver
```

Recommended sample data:

- Admin/librarian demo account: `sample_admin` or `sample_librarian`
- Member: `STU-2026-001`
- Book: `Clean Code`
- Category: `Computer Science`
- Author: `Robert C. Martin`
- Publisher: `Pearson Education`
- Fine status: unpaid or partially paid
- Report type: books or borrowing

For the live deployed site, only run `seed_data` if the Supabase production database is empty or specifically prepared for demonstration.

## Privacy and Security Checklist

Do not show:

- Password fields containing visible values
- Supabase service-role key
- Supabase anon key
- Django `SECRET_KEY`
- Database password
- `.env` file
- Access tokens
- Refresh tokens
- Browser password manager popups
- Real student/member personal data
- Real admin production password

Safe to show:

- Public deployed URL
- Demo usernames
- Demo-only emails
- Table names
- Non-sensitive row counts
- Test result summary
- Render service status page without environment variables

## Backup Screenshots if Live System Fails

Store fallback images in `99_Backup_Screenshots/`.

Recommended backup set:

| Backup File | Purpose |
| --- | --- |
| `backup_01_login_page.png` | Use if public site is temporarily offline |
| `backup_02_dashboard.png` | Use if dashboard cannot load during demo |
| `backup_03_books_members.png` | Use for catalog/member proof |
| `backup_04_borrow_return_fine.png` | Use for circulation workflow proof |
| `backup_05_notifications_reports.png` | Use for notification/report proof |
| `backup_06_supabase_tables.png` | Use if Supabase dashboard is slow |
| `backup_07_test_results.png` | Use if tests take too long live |
| `backup_08_render_deployment.png` | Use if Render dashboard is unavailable |

## Final Evidence Table

| Screenshot No. | Feature | Lecturer Objective | Test Status | File Name |
| --- | --- | --- | --- | --- |
| 01 | Login page | Authentication, static files, UI | Pending screenshot | `01_Public_Auth/01_login_page_library_image.png` |
| 02 | Registration page | User registration, Supabase Auth | Pending screenshot | `01_Public_Auth/02_registration_page.png` |
| 03 | Dashboard | Statistics and analytics | Pending screenshot | `02_Core_System/03_dashboard_statistics.png` |
| 04 | User and role management | RBAC and user management | Pending screenshot | `02_Core_System/04_user_role_management.png` |
| 05 | Category management | Book classification | Pending screenshot | `02_Core_System/05_category_management.png` |
| 06 | Author management | Author records | Pending screenshot | `02_Core_System/06_author_management.png` |
| 07 | Publisher management | Publisher records | Pending screenshot | `02_Core_System/07_publisher_management.png` |
| 08 | Book management | Book registration, stock, status | Pending screenshot | `02_Core_System/08_book_management.png` |
| 09 | Member management | Student/teacher/staff members | Pending screenshot | `02_Core_System/09_member_management.png` |
| 10 | Borrow book | Borrowing workflow | Pending screenshot | `03_Circulation_Fines/10_borrow_book_process.png` |
| 11 | Return book | Returning workflow | Pending screenshot | `03_Circulation_Fines/11_return_book_process.png` |
| 12 | Overdue record | Due-date and overdue tracking | Pending screenshot | `03_Circulation_Fines/12_overdue_record.png` |
| 13 | Fine calculation | Automatic late-return fine | Pending screenshot | `03_Circulation_Fines/13_fine_calculation.png` |
| 14 | Notifications | Member notification history | Pending screenshot | `03_Circulation_Fines/14_notification_page.png` |
| 15 | Reports | Reports and generated_by relationship | Pending screenshot | `04_Reports_Search/15_reports_page.png` |
| 16 | Search/filtering | Search by title, ISBN, author, category, status | Pending screenshot | `04_Reports_Search/16_search_filtering.png` |
| 17 | Supabase Auth users | Supabase Auth integration | Pending screenshot | `05_Supabase_Evidence/17_supabase_auth_users.png` |
| 18 | Supabase database tables | 11-table Data Dictionary compliance | Pending screenshot | `05_Supabase_Evidence/18_supabase_11_tables.png` |
| 19 | Django test results | Testing and quality assurance | Pending screenshot | `06_Testing_Deployment/19_django_test_results.png` |
| 20 | Render deployed website | Online deployment | Pending screenshot | `06_Testing_Deployment/20_render_deployed_website.png` |

## Final Notes for Report Captions

Use short captions under each screenshot. Example:

> Figure 1: Login page with professional library image and Supabase-ready authentication form.

Avoid long explanations below screenshots. Put detailed explanations in the system workflow or testing section instead.

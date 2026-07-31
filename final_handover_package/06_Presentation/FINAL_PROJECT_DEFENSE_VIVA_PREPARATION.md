# Final Project Defense Viva Preparation

Project: Enterprise Library Management System  
Backend: Django  
Database: Supabase PostgreSQL  
Authentication: Supabase Auth  
Frontend: Bootstrap 5  
Deployment: Render  
Required Business Schema: Lecturer's 11-table Library Management System Data Dictionary

---

## A. 100 Professional Viva Questions

Use these questions to rehearse short, confident answers. In the defense, answer directly first, then add one example from your system.

| No. | Viva Question | Ideal Answer | Why This Is Correct | Common Mistake |
| --- | --- | --- | --- | --- |
| 1 | What is your project about? | My project is a web-based Library Management System for managing users, roles, books, members, borrowing, returning, fines, notifications, and reports. | It summarizes the system scope clearly. | Giving only a technology answer instead of explaining the business problem. |
| 2 | Why did you choose this project? | I chose it because manual library work can cause lost records, slow searching, inaccurate fines, and poor stock tracking. | It links the project to a real problem. | Saying only "because it is easy" or "because it is required." |
| 3 | What is the main objective? | The main objective is to computerize library operations and improve accuracy, speed, reporting, and access control. | It matches the lecturer's objectives. | Listing features without explaining the goal. |
| 4 | Who are the users of the system? | Admins, librarians, assistant librarians, students, teachers, staff, and guests or visitors. | These match the role design. | Forgetting non-admin users. |
| 5 | What are the main modules? | Authentication, role/user management, catalog management, member management, borrowing, returning, fines, notifications, dashboard, and reports. | These are the implemented business modules. | Claiming unsupported modules such as online payment. |
| 6 | What problem does the system solve? | It reduces manual recording errors, improves book availability tracking, automates fines, and provides faster reporting. | It connects features to library pain points. | Only saying "it stores books." |
| 7 | What is your technology stack? | Django for backend, Supabase PostgreSQL for database, Supabase Auth for authentication, Bootstrap 5 for frontend, and Render for deployment. | It accurately describes the actual architecture. | Mixing up Supabase database and Supabase Auth. |
| 8 | Why did you use Django? | Django provides models, forms, templates, admin, authentication support, ORM, security protections, and fast development. | It explains framework benefits. | Saying Django is only for frontend. |
| 9 | Why did you use PostgreSQL? | PostgreSQL supports relational integrity, foreign keys, constraints, indexes, and production reliability. | Library data needs reliable relationships. | Saying PostgreSQL is the same as Excel. |
| 10 | Why did you use Supabase? | Supabase provides hosted PostgreSQL and authentication, making the project easier to deploy and verify online. | It explains Supabase's role. | Saying Supabase replaces Django. |
| 11 | What does Supabase Auth do in your project? | It handles email and password authentication, while Django keeps the local users table for roles and profiles. | This preserves the 11-table schema. | Deleting or ignoring the local users table. |
| 12 | What does the Django users table do? | It stores username, email, full name, role, status, and profile-related data for authorization. | It separates authentication from authorization. | Thinking Supabase Auth stores local roles. |
| 13 | What is role-based access control? | RBAC restricts features based on the user's assigned role, such as Admin or Librarian. | It is the correct security model for this system. | Allowing every logged-in user to access all pages. |
| 14 | What is the lecturer's required Data Dictionary? | It is the required 11-table business schema: roles, users, categories, authors, publishers, books, members, borrow_records, fines, notifications, and reports. | It proves schema compliance. | Adding prohibited business tables. |
| 15 | Does your active system use BookCopy? | No. BorrowRecord uses a direct book_id foreign key to books as required. | This matches the lecturer's correction. | Mentioning older phase design with BookCopy. |
| 16 | What is the primary key of users? | The primary key is user_id. | It matches the required schema. | Saying id instead of user_id. |
| 17 | What is the primary key of borrow_records? | The primary key is borrow_id. | It matches the Data Dictionary. | Saying record_id or id. |
| 18 | Which table stores book details? | The books table stores ISBN, title, category, author, publisher, quantity, available quantity, shelf location, and status. | It explains catalog data. | Confusing books with borrow_records. |
| 19 | Which table stores member details? | The members table stores member profile information linked to users through user_id. | It explains user/member separation. | Treating every user as a member automatically without profile. |
| 20 | What is the difference between a user and a member? | A user is a system login/profile record; a member is a library membership profile linked to a user. | It clarifies database design. | Using the terms interchangeably. |
| 21 | What is the role of the roles table? | It stores role names and descriptions used for access control. | It supports RBAC. | Hard-coding all permissions only in templates. |
| 22 | What is the role of the categories table? | It classifies books by subject or type. | It supports organized catalog search. | Storing category as plain text in books only. |
| 23 | What is the role of authors? | It stores book author information and links books to authors. | It avoids repeated author names. | Duplicating author text in every book row. |
| 24 | What is the role of publishers? | It stores publisher information and links books to publishers. | It normalizes publisher data. | Putting publisher data only inside the book title. |
| 25 | How does borrowing work? | A librarian selects a member and book, enters borrow and due dates, and the system creates a borrow_record and reduces available quantity. | It describes the actual workflow. | Forgetting stock updates. |
| 26 | How does returning work? | The system records return date and received_by user, updates status, increases available quantity, and creates a fine if late. | It covers full return logic. | Only setting status to returned. |
| 27 | How is a late return detected? | The return date or current date is compared with the due date. If it is after due date, overdue days are calculated. | Correct basis for fine calculation. | Comparing only borrow date with return date. |
| 28 | How is the fine calculated? | Fine equals overdue days multiplied by the configured fine rate. | It is simple and auditable. | Using a fixed fine for every case. |
| 29 | Which table stores fines? | The fines table stores borrow_id, member_id, amount, paid_amount, status, and paid date. | It matches the required table. | Creating a separate payments table for this assignment. |
| 30 | Why does Fine connect to both BorrowRecord and Member? | BorrowRecord identifies the transaction, while Member identifies who owes the fine. | It improves reporting and validation. | Linking fine only to book. |
| 31 | Which table stores notifications? | The notifications table stores member notifications such as due-date, overdue, fine, and general messages. | It matches member notification history. | Linking notifications only to users. |
| 32 | Why does Notification use member_id instead of user_id? | The lecturer required notifications to connect to members, and library notices belong to membership activity. | It proves schema compliance. | Using user_id because login uses users. |
| 33 | Which table stores reports? | The reports table stores report type, generated_by user, generated time, and file path. | It tracks report history. | Generating files without storing metadata. |
| 34 | Why does Report connect to generated_by? | It records which staff user generated the report for accountability. | It supports audit and accountability. | Leaving reports anonymous. |
| 35 | What is a foreign key? | A foreign key connects a child table record to a valid parent table record. | It defines relational integrity. | Saying it is only a label. |
| 36 | What is the foreign key from books to categories? | books.category_id references categories.category_id. | It matches the ERD. | Saying category_name is the foreign key. |
| 37 | What is the foreign key from books to authors? | books.author_id references authors.author_id. | It matches the Data Dictionary. | Storing author text only. |
| 38 | What is the foreign key from books to publishers? | books.publisher_id references publishers.publisher_id. | It matches the Data Dictionary. | Forgetting publisher relationship. |
| 39 | What does borrow_records.book_id reference? | It references books.book_id. | Required by the lecturer. | Saying BookCopy. |
| 40 | What does borrow_records.issued_by reference? | It references users.user_id for the staff user who issued the book. | It records accountability. | Using member_id for issued_by. |
| 41 | What does borrow_records.received_by reference? | It references users.user_id for the staff user who received the returned book. | It records return accountability. | Making it required before return. |
| 42 | Why is received_by nullable? | It is empty until the book is returned. | Borrowed records do not yet have a receiving user. | Forcing received_by during borrowing. |
| 43 | What is an ERD? | An Entity Relationship Diagram shows tables, primary keys, foreign keys, and relationships. | It explains database structure visually. | Drawing only page navigation. |
| 44 | What is normalization? | It organizes data to reduce duplication and improve consistency. | The schema separates roles, authors, publishers, and categories. | Repeating all text fields in one large table. |
| 45 | Why not store everything in one table? | It would cause duplication, update errors, and weak data integrity. | Relational design is better for this system. | Thinking fewer tables always means better design. |
| 46 | What is Django MVT architecture? | Model handles data, View handles request logic, and Template handles presentation. | Django uses MVT, similar to MVC. | Calling templates controllers. |
| 47 | What is the role of models.py? | It defines database tables, fields, relationships, validation, and model behavior. | It is the data layer. | Putting all business logic in templates. |
| 48 | What is the role of views.py? | It handles requests, queries data, applies business logic, and returns responses. | It is the request-handling layer. | Making views only return static pages. |
| 49 | What is the role of templates? | Templates render HTML pages using context from views. | It separates UI from backend logic. | Writing database queries inside templates. |
| 50 | What is the role of urls.py? | It maps URL paths to Django views. | It controls routing. | Hard-coding links without URL names. |
| 51 | What is the role of forms.py? | It defines input fields, validation, and cleaned data for create/update actions. | Forms protect input quality. | Trusting raw POST data directly. |
| 52 | What is the role of admin.py? | It configures how models appear and are managed in Django Admin. | Admin supports staff management. | Treating admin as the whole application. |
| 53 | Why use Django forms instead of plain HTML only? | Forms provide validation, cleaned data, error messages, and model integration. | Safer and more maintainable. | Validating only with JavaScript. |
| 54 | What validation exists for books? | ISBN is normalized, available quantity cannot exceed quantity, and publication year cannot be in the future. | It protects data correctness. | Allowing negative stock. |
| 55 | What validation exists for borrow records? | Due date must be after borrow date, return date cannot be before borrow date, and returned records need return date and received_by. | It protects transaction integrity. | Allowing returned records without receiver. |
| 56 | What validation exists for fines? | Fine amount and paid amount cannot be negative, paid amount cannot exceed amount, and paid fines need paid date. | It protects financial data. | Allowing paid amount greater than fine. |
| 57 | How do you prevent SQL injection? | I use Django ORM and forms instead of raw string SQL. | ORM parameterizes queries. | Manually building SQL with user input. |
| 58 | How do you prevent XSS? | Django templates escape output by default, and user input is validated. | Django includes default XSS protection. | Marking user input as safe unnecessarily. |
| 59 | How do you handle CSRF? | Django CSRF middleware protects POST forms using CSRF tokens. | Correct Django practice. | Disabling CSRF to fix form errors. |
| 60 | How do you protect secrets? | Secrets are stored in environment variables and `.env` is excluded from Git. | It avoids exposing credentials. | Pasting keys in settings.py or README. |
| 61 | What production setting is important for DEBUG? | DEBUG must be False in production. | It prevents exposing error details. | Deploying with DEBUG=True. |
| 62 | What are ALLOWED_HOSTS? | Allowed hostnames that Django will serve. | Prevents host header attacks. | Setting it to `*` permanently. |
| 63 | What are CSRF_TRUSTED_ORIGINS? | Trusted origins allowed for secure POST requests. | Needed for deployed domains. | Missing scheme such as https://. |
| 64 | Why use secure cookies? | They ensure session and CSRF cookies are sent only over HTTPS in production. | Improves session security. | Using insecure cookies on a public site. |
| 65 | Why use WhiteNoise? | It serves static files efficiently in production for Django apps. | Common Render deployment practice. | Expecting Django dev static serving in production. |
| 66 | Why use Gunicorn? | Gunicorn is a production WSGI server for running Django. | Django runserver is not for production. | Deploying with runserver. |
| 67 | Why deploy on Render? | Render supports web services, environment variables, build commands, and Gunicorn deployment. | It is suitable for student web deployment. | Thinking Render stores the database automatically. |
| 68 | How does Django connect to Supabase PostgreSQL? | Through PostgreSQL settings or DATABASE_URL using host, port, user, password, database, and sslmode=require. | It describes the database connection. | Exposing the password in source code. |
| 69 | Why is sslmode=require important? | It encrypts the database connection to Supabase. | Supabase production connections require secure transport. | Leaving SSL off. |
| 70 | What is a migration? | A migration is Django's versioned database schema change file. | It keeps database schema reproducible. | Editing production tables manually without migrations. |
| 71 | What command runs migrations? | `python manage.py migrate`. | It applies schema changes. | Running only makemigrations. |
| 72 | What command checks pending migration changes? | `python manage.py makemigrations --check --dry-run`. | It verifies model/migration consistency. | Ignoring migration drift. |
| 73 | What command runs tests? | `python manage.py test`. | It runs the Django test suite. | Only testing manually in browser. |
| 74 | What did your final tests show? | The final suite passed 30 tests. | It is actual project evidence. | Claiming 100% coverage without proof. |
| 75 | What types of tests did you write? | Schema, relationships, borrowing, return, fine, notification, report, seed data, Supabase Auth, and RBAC tests. | It covers main risks. | Testing only page loading. |
| 76 | What is seed data? | Demo data inserted by a management command for testing and presentation. | It supports repeatable demos. | Manually adding random data every time. |
| 77 | Why is seed data repeatable? | It avoids duplicate records when run again. | Good maintenance practice. | Creating duplicates on every run. |
| 78 | What is the dashboard for? | It shows statistics such as total books, members, borrowing records, overdue items, and fines. | It supports decision-making. | Treating dashboard as decoration only. |
| 79 | What reports are implemented? | CSV-style report generation and report history for core data such as books, members, borrowing, and fines. | It matches current implementation. | Claiming PDF/Excel if not implemented. |
| 80 | How is search implemented conceptually? | The system filters records by fields such as title, ISBN, author, category, and status. | It helps users find data quickly. | Searching only exact title. |
| 81 | What makes your UI responsive? | Bootstrap 5 grid, responsive components, tables, cards, navigation, and custom CSS. | Bootstrap provides responsive behavior. | Testing only desktop view. |
| 82 | Why add a library image to login? | It improves branding and makes the system look professional for users and presentation. | UI supports user confidence. | Using a heavy image that breaks loading. |
| 83 | How do you show success or error messages? | Django messages and Bootstrap alerts show feedback after actions. | Feedback improves UX. | Failing silently. |
| 84 | What is a 500 error? | A server-side error, often from missing env variables, database errors, or code exceptions. | It identifies likely production issues. | Saying it is always internet problem. |
| 85 | What is an invalid host header error? | Django rejects requests from domains not in ALLOWED_HOSTS. | Common deployment issue. | Disabling security instead of configuring hosts. |
| 86 | What is CSRF verification failed? | Django rejected a POST request from an untrusted or missing CSRF source. | It protects against forged requests. | Removing CSRF middleware. |
| 87 | How do you verify Supabase tables? | Use Supabase Table Editor or SQL queries to check the 11 required table names. | It proves deployment database compliance. | Only checking local SQLite. |
| 88 | What safe SQL can show table names? | Query information_schema for public table names. | It avoids exposing data. | Screenshotting secrets or connection strings. |
| 89 | What is the most important database relationship? | borrow_records links members, books, issued_by user, and received_by user. | It represents circulation accountability. | Linking borrowing only to books. |
| 90 | How do you handle unavailable books? | Borrowing is prevented when available quantity is zero or status is not available. | Prevents invalid borrowing. | Allowing negative availability. |
| 91 | How does returning affect book status? | It increases available quantity and preserves special statuses like damaged when appropriate. | Avoids overwriting important status. | Always setting status to available. |
| 92 | What is the purpose of indexes? | Indexes improve query performance for common filters such as status, due date, member, and book. | It supports performance. | Adding indexes randomly to every field. |
| 93 | What is select_related? | It fetches related foreign-key objects in one query. | Reduces N+1 queries. | Using it for many-to-many without understanding. |
| 94 | What is pagination? | Pagination splits long lists into pages. | Improves usability and performance. | Loading thousands of rows at once. |
| 95 | What challenge did you face? | Aligning Supabase Auth with the lecturer's users table without changing the 11-table schema. | It is a real architectural challenge. | Giving a vague answer like "coding was hard." |
| 96 | How did you solve that challenge? | Supabase Auth handles authentication, while Django users store roles/profile and are synced by email. | It preserves both requirements. | Creating duplicate conflicting user systems. |
| 97 | What would you improve next? | Add PDF/Excel reports, email reminders, barcode scanning, cloud media storage, and advanced analytics. | Good future roadmap. | Claiming these are already complete. |
| 98 | What is your strongest feature? | The corrected 11-table schema with complete borrowing, returning, fine, notification, and reporting workflow. | It highlights compliance and functionality. | Focusing only on UI colors. |
| 99 | How would you demonstrate the system? | Login, show dashboard, add catalog data, add member, borrow, return, fine, notification, report, then show Supabase tables and tests. | It is a logical demo flow. | Starting with code before showing working features. |
| 100 | Why should this project pass? | It satisfies the required 11-table schema, implements key library workflows, includes tests, documentation, Supabase integration, and deployment readiness. | It summarizes academic value. | Overclaiming features not implemented. |

---

## B. 20 Scenario-Based Debugging or Modification Questions

| No. | Scenario Question | Strong Defense Answer | What the Lecturer Wants to Hear |
| --- | --- | --- | --- |
| 1 | Login fails after deployment. What do you check first? | I check Render logs, environment variables, Supabase URL/key, ALLOWED_HOSTS, CSRF trusted origins, and Supabase Auth settings. | Structured debugging, not guessing. |
| 2 | Static files do not load on Render. What do you do? | I check WhiteNoise settings, STATIC_ROOT, collectstatic output, build logs, and static file paths. | Understanding production static handling. |
| 3 | Borrowing creates negative available quantity. How would you fix it? | Add validation before issuing a book and keep database constraints preventing invalid quantities. | Data integrity protection. |
| 4 | A returned book has no received_by user. What is wrong? | Return validation should require received_by when status is returned. | Correct return accountability. |
| 5 | Supabase database connection times out. What do you check? | Check host, port, SSL mode, password, network access, and whether direct or pooler connection is needed. | Supabase deployment awareness. |
| 6 | Lecturer says extra tables appear in Supabase. How do you explain? | Django framework tables may exist, but the business Data Dictionary tables remain exactly 11. | Distinguishing framework tables from business tables. |
| 7 | A student can open user management. What would you inspect? | Check role capability logic, decorators, template links, and view-level permission checks. | Authorization must be enforced in views. |
| 8 | Fine amount is wrong. What do you inspect? | Check due_date, return_date, days_overdue calculation, and fine rate setting. | Trace calculation inputs. |
| 9 | Report file upload accepts `.txt`. What should happen? | The form should reject disallowed extensions and show a validation error. | File validation. |
| 10 | Notification appears for the wrong member. What do you inspect? | Check notification.member_id and query filtering by current user's member profile. | Member-level data privacy. |
| 11 | Dashboard is slow. What do you optimize? | Use aggregate counts, select_related, indexes, and avoid unnecessary loops. | Performance thinking. |
| 12 | `makemigrations --check` detects changes. What does it mean? | Models and migrations are out of sync, so migrations must be reviewed and created if valid. | Migration discipline. |
| 13 | A book with future publication year is accepted. What do you fix? | Add or repair model/form validation to reject future years. | Input validation. |
| 14 | Admin forgot password. What is the safe recovery? | Use secure password reset or createsuperuser/change password command, not editing hashes manually. | Safe admin recovery. |
| 15 | `.env` was accidentally pushed to GitHub. What do you do? | Remove it, rotate all exposed secrets, rewrite history if necessary, and update `.gitignore`. | Security incident handling. |
| 16 | Render build fails installing packages. What do you check? | Python version, requirements.txt, build logs, package compatibility, and build command. | Deployment troubleshooting. |
| 17 | Supabase Auth user exists but local Django user does not. What happens? | Depending on configuration, the system can sync a local user or block login if local user is required. | Auth/profile separation. |
| 18 | Member has unpaid fine but can borrow again. What would you add? | Add a borrowing rule checking unpaid fines before issuing. | Policy enforcement. |
| 19 | Lecturer asks to add Excel reports. How would you approach? | Add an export service using a package like openpyxl without changing the 11-table schema. | Extensible design. |
| 20 | Production shows 500 error. What is your process? | Check logs, reproduce safely, inspect env variables, database connection, migrations, and recent changes. | Calm debugging process. |

---

## C. 20 Practical Coding Questions Related to the Project

These are practical coding-defense prompts. You do not need to write full code in the viva unless asked; explain the correct approach.

| No. | Coding Question | Ideal Practical Answer | Common Mistake |
| --- | --- | --- | --- |
| 1 | How would you query all borrowed records with member and book data efficiently? | Use `BorrowRecord.objects.select_related("member", "book", "issued_by", "received_by")`. | Querying related objects inside a loop. |
| 2 | How would you filter books by title search? | Use a case-insensitive filter such as title contains the search term. | Using exact match only. |
| 3 | How would you prevent borrowing when stock is zero? | Validate `available_quantity > 0` and book status before saving the borrow record. | Decreasing stock without checking. |
| 4 | How would you update stock after borrowing? | Decrement `available_quantity` inside the borrowing workflow after validation. | Updating stock before validation. |
| 5 | How would you update stock after returning? | Set return fields, then increment available quantity within valid limits. | Increasing beyond total quantity. |
| 6 | How would you calculate overdue days? | Compare `return_date` or today's date with `due_date` and use max(days, 0). | Allowing negative overdue days. |
| 7 | How would you create a fine after late return? | If overdue days > 0, create Fine linked to borrow and member. | Creating fine without borrow link. |
| 8 | How would you protect a view for librarians only? | Use login-required plus a role/capability check in the view or decorator. | Hiding the menu only. |
| 9 | How would you create a ModelForm for Book? | Use a Django ModelForm with model Book and allowed fields. | Accepting all fields blindly. |
| 10 | How would you validate paid_amount? | Ensure paid_amount is not negative and not greater than amount. | Trusting frontend validation only. |
| 11 | How would you define a URL for book editing? | Create a path with book_id parameter mapped to the edit view. | Hard-coding primary key names inconsistently. |
| 12 | How would you show form errors in templates? | Render Django form errors near fields and global non-field errors. | Ignoring validation messages. |
| 13 | How would you generate a CSV report? | Query the required records, write CSV rows, save file path, and create Report metadata. | Generating file without Report record. |
| 14 | How would you test the borrow workflow? | Create sample role, user, member, book, post to borrow view, assert record and stock change. | Only checking HTTP 200. |
| 15 | How would you test Supabase Auth without real network calls? | Mock the Supabase service response in Django tests. | Calling real Supabase in unit tests. |
| 16 | How would you check database table names in tests? | Assert each model's `_meta.db_table` equals the required table name. | Looking manually only. |
| 17 | How would you block inactive users? | Check `is_active` during login validation and deny access with an error message. | Letting inactive users log in. |
| 18 | How would you use environment variables in settings? | Read secret, database, and Supabase values from env or decouple/environ. | Hard-coding credentials. |
| 19 | How would you run a management command for sample data? | Create a command under `management/commands` and run `python manage.py seed_data`. | Creating sample data in migrations. |
| 20 | How would you avoid N+1 queries in lists? | Use `select_related` for foreign keys and pagination for large lists. | Rendering unbounded querysets. |

---

## D. 20 Database Questions Using the 11-Table Schema

| No. | Database Question | Ideal Answer | Why It Matters |
| --- | --- | --- | --- |
| 1 | List the 11 required tables. | roles, users, categories, authors, publishers, books, members, borrow_records, fines, notifications, reports. | Proves Data Dictionary knowledge. |
| 2 | What is the primary key of roles? | role_id. | Required naming compliance. |
| 3 | What is the primary key of books? | book_id. | Required naming compliance. |
| 4 | What does users.role_id reference? | roles.role_id. | Role assignment. |
| 5 | What does members.user_id reference? | users.user_id. | Links user account to member profile. |
| 6 | What does books.category_id reference? | categories.category_id. | Book classification. |
| 7 | What does books.author_id reference? | authors.author_id. | Author relationship. |
| 8 | What does books.publisher_id reference? | publishers.publisher_id. | Publisher relationship. |
| 9 | What does borrow_records.member_id reference? | members.member_id. | Borrower relationship. |
| 10 | What does borrow_records.book_id reference? | books.book_id. | Borrowed book relationship. |
| 11 | What does borrow_records.issued_by reference? | users.user_id. | Staff issuing accountability. |
| 12 | What does borrow_records.received_by reference? | users.user_id. | Staff receiving accountability. |
| 13 | What does fines.borrow_id reference? | borrow_records.borrow_id. | Fine transaction source. |
| 14 | What does fines.member_id reference? | members.member_id. | Fine owner. |
| 15 | What does notifications.member_id reference? | members.member_id. | Notification recipient. |
| 16 | What does reports.generated_by reference? | users.user_id. | Report accountability. |
| 17 | Why is available_quantity stored in books? | It tracks current stock availability for borrowing decisions. | Prevents over-borrowing. |
| 18 | Why is status stored in books? | It tracks whether a book is available, borrowed, lost, damaged, or under repair. | Supports operational decisions. |
| 19 | Why use constraints on quantity? | To prevent negative quantity and available quantity above total quantity. | Protects data integrity. |
| 20 | How do you prove schema compliance? | Show models, migrations, Supabase table list, and tests verifying table and key names. | Strong defense evidence. |

---

## E. Lecturer-Style Evaluation

| Area | Score | Lecturer Comment |
| --- | --- | --- |
| Technical Score | 88 / 100 | Strong Django implementation with working workflows, tests, deployment readiness, and Supabase integration. |
| Database Score | 92 / 100 | Correct 11-table business schema, explicit primary keys, foreign keys, constraints, and relationship tests. |
| UI/UX Score | 84 / 100 | Clean Bootstrap 5 interface, responsive layout, dashboard, forms, tables, and branded login page. |
| Documentation Score | 90 / 100 | Strong final report, user manual, deployment guide, screenshots plan, and handover package. |
| Presentation Score | 86 / 100 | Clear demo flow; score can improve by inserting real screenshots and rehearsing the live demonstration. |
| Overall Score | 88 / 100 | A complete and defendable university final project with strong data compliance and practical implementation. |

### Suggested Lecturer Feedback

The project is technically strong and meets the main academic requirements. The strongest part is the corrected 11-table Data Dictionary and the connection between borrowing, returning, fines, notifications, and reports. The system also demonstrates modern deployment and authentication using Supabase and Render. The main improvement areas are adding actual screenshots to the report, preparing a smooth live demo, and clearly explaining the difference between Supabase Auth users and the local Django users table.

---

## F. How to Answer Confidently During Defense

1. Answer the question directly first.
2. Use the exact table names when discussing the database.
3. Say "Supabase Auth handles authentication; Django users table handles role/profile authorization" whenever authentication is discussed.
4. Do not claim features that are not implemented.
5. If asked about a limitation, admit it and explain a future improvement.
6. If asked to debug, explain your process: logs, environment variables, database, migrations, tests, then code.
7. Use examples from your system: `borrow_records.book_id`, `issued_by`, `received_by`, `notifications.member_id`, and `reports.generated_by`.
8. Keep answers short: definition, project example, benefit.
9. If you do not know an answer, say how you would investigate it.
10. Stay calm and speak as the developer who understands the design decisions.

---

## G. What to Demonstrate First

Start with the working system, not the source code.

Recommended demonstration order:

1. Open the deployed Render website.
2. Show the login page with the library image.
3. Login using a demo admin or librarian account.
4. Show dashboard statistics.
5. Show the 11 required tables in Supabase.
6. Manage category, author, publisher, and book.
7. Manage a member.
8. Borrow a book.
9. Return the book.
10. Show automatic fine calculation.
11. Show notification history.
12. Generate or view a report.
13. Show search and filtering.
14. Show role-based access by logging in as a lower-permission user.
15. Show final Django test result screenshot or terminal output.

### Strong Closing Statement

"This Library Management System satisfies the lecturer's required 11-table Data Dictionary and implements the main university library workflow from book registration to borrowing, returning, fine calculation, notifications, reporting, testing, and deployment. Supabase Auth is used only for authentication, while Django keeps the required users and roles for authorization. The system is tested, documented, and ready for final demonstration."


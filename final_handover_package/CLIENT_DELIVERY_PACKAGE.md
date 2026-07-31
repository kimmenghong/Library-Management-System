# Enterprise Library Management System

## Client Delivery Package

Project stack: Python Django, Supabase PostgreSQL, Supabase Auth, Bootstrap 5, Render Deployment  
Release scope: Existing Version 1.0 implementation  
Database rule: The lecturer-required 11-table Data Dictionary remains unchanged.

---

## 1. Executive Summary

The Enterprise Library Management System is a web-based application designed to help a library manage daily operations such as book cataloging, member management, borrowing, returning, fine calculation, notifications, reporting, and role-based access control.

The system is built with Python Django for the backend, Supabase PostgreSQL for the hosted database, Supabase Auth for email/password authentication, Bootstrap 5 for the user interface, and Render for deployment. The implemented version follows the required 11-table library database structure: `roles`, `users`, `categories`, `authors`, `publishers`, `books`, `members`, `borrow_records`, `fines`, `notifications`, and `reports`.

Key business benefits include reduced manual paperwork, better book availability tracking, faster search, controlled staff access, automatic fine calculation, and improved reporting for library decision-making.

Current limitations include no active reservation queue, no RFID integration, no online payment gateway, no native mobile app, and no full backend PDF/Excel reporting. These are recommended as future roadmap items.

The system is suitable for academic delivery, demonstration, and small-library pilot use after final deployment verification and client sign-off.

---

## 2. Client Acceptance Test (UAT)

### 2.1 Acceptance Checklist

| No. | Acceptance Item | Expected Result | Status |
| --- | --- | --- | --- |
| 1 | Login page opens | User can access login page with library image | Pending |
| 2 | Supabase Auth login works | Valid user can log in successfully | Pending |
| 3 | Logout works | User can end session safely | Pending |
| 4 | Dashboard loads | Statistics display correctly | Pending |
| 5 | User and role management works | Admin can manage users and roles | Pending |
| 6 | Book management works | Staff can add, edit, search, and delete allowed book records | Pending |
| 7 | Member management works | Staff can manage student, teacher, staff, and librarian members | Pending |
| 8 | Borrowing works | Book issue creates borrow record and updates availability | Pending |
| 9 | Returning works | Return records receiver and updates availability | Pending |
| 10 | Fine calculation works | Late return creates correct fine | Pending |
| 11 | Notifications work | Member notifications are created and displayed | Pending |
| 12 | Reports work | Staff can generate and download report files | Pending |
| 13 | Role permissions work | Unauthorized users cannot access restricted pages | Pending |
| 14 | Static files load | CSS, JavaScript, logo, favicon, and login image display | Pending |
| 15 | Database matches 11-table schema | Supabase shows required business tables | Pending |

### 2.2 UAT Test Scenarios

| Scenario | Steps | Expected Result |
| --- | --- | --- |
| Admin login | Open system, enter admin credentials, submit login form | Admin reaches dashboard |
| Librarian catalog task | Login as librarian, add category, author, publisher, and book | New book appears in book list |
| Member registration | Add a user/member profile | Member appears in member list |
| Borrow book | Select active member and available book, enter dates, issue book | Borrow record created, book availability decreases |
| Return book on time | Return an active borrow record before due date | Status becomes returned, no fine created |
| Return book late | Return a book after due date | Fine record and notification are created |
| Search books | Search by title, ISBN, author, category, or status | Matching books are displayed |
| Report generation | Generate books, members, borrowing, or fines report | Report record is created with downloadable file |
| Unauthorized access | Login as member and try to open user management | Access is denied |
| Responsive UI | Open dashboard/books on mobile screen | Layout remains usable |

### 2.3 UAT Sign-Off Template

Client Name: ______________________________  
Organization: ______________________________  
Project: Enterprise Library Management System  
Version: 1.0.0  
UAT Date: _________________________________

I confirm that the Library Management System has been demonstrated and tested against the agreed acceptance checklist.

Decision:

- [ ] Accepted
- [ ] Accepted with minor issues
- [ ] Rejected pending fixes

Client Representative Name: ______________________________  
Signature: ______________________________  
Date: ______________________________

Project Representative Name: ______________________________  
Signature: ______________________________  
Date: ______________________________

---

## 3. Training Materials

### 3.1 Administrator Training Guide

Administrators are responsible for system setup, user management, role assignment, database supervision, and final operational approval.

Admin tasks:

1. Log in using an administrator account.
2. Open the dashboard and review system statistics.
3. Manage roles and users.
4. Assign correct roles to librarians, assistants, students, teachers, and staff.
5. Review book, member, borrowing, fine, notification, and report pages.
6. Monitor deployment, database connection, and system logs.
7. Ensure backups are created and stored securely.
8. Review security settings and inactive accounts regularly.

Admin rules:

- Do not share administrator credentials.
- Do not expose `.env`, database passwords, Supabase keys, or secret keys.
- Disable inactive accounts.
- Use demo accounts only for training and presentations.

### 3.2 Librarian Training Guide

Librarians manage daily library operations.

Librarian tasks:

1. Log in using a librarian account.
2. Add and update book categories.
3. Add and update authors and publishers.
4. Register books with ISBN, title, stock quantity, shelf location, and status.
5. Register or update library members.
6. Issue books to active members.
7. Return books and verify return date.
8. Review fines for late returns.
9. Create or review member notifications.
10. Generate reports for management review.

Operational reminders:

- Check book availability before issuing.
- Confirm member status is active.
- Verify due dates carefully.
- Review fine amount after late return.
- Do not delete records that are part of borrowing history.

### 3.3 Member Quick-Start Guide

Members can use the system to view available books, borrowing information, fines, and notifications where access is permitted.

Member steps:

1. Open the library system URL.
2. Log in using the provided member credentials.
3. View the dashboard or available menu items.
4. Search books by title, ISBN, author, category, or status.
5. Review borrowing records.
6. Review fines if any exist.
7. Read notifications.
8. Log out after use.

### 3.4 Frequently Asked Questions

| Question | Answer |
| --- | --- |
| Can members borrow books directly? | In Version 1.0, staff issue books through the borrowing workflow. |
| Does the system support reservations? | Not in the current 11-table Version 1.0 release. It is recommended for Version 2.0. |
| Does the system support online fine payment? | Not in Version 1.0. Fine payment can be recorded by authorized staff. |
| Does the system send real push notifications? | Version 1.0 stores notification history. Push notification is a future enhancement. |
| Can the database run on Supabase? | Yes, production configuration supports Supabase PostgreSQL with SSL. |
| Is Supabase Auth used? | Yes, Supabase Auth can handle email/password authentication while Django keeps roles and profiles. |
| Can the system be used offline? | The deployed system requires internet access. Screenshots and local SQLite can support demonstrations if needed. |
| Can the 11-table schema be changed? | Not for the submitted Version 1.0. Changes should be planned for a future version. |

---

## 4. Service Level Agreement (SLA)

### 4.1 Support Hours

Standard support hours:

```text
Monday to Friday
9:00 AM to 5:00 PM
Excluding public holidays
```

Emergency support may be arranged separately for production clients.

### 4.2 Bug Severity Levels

| Severity | Description | Example | Target Response |
| --- | --- | --- | --- |
| Critical | System unavailable or data loss risk | Website down, database inaccessible | 4 business hours |
| High | Major feature unusable | Borrowing or login fails | 1 business day |
| Medium | Feature partially affected | Report download problem | 2 business days |
| Low | Minor issue or cosmetic problem | Text alignment, typo | 5 business days |

### 4.3 Maintenance Schedule

| Maintenance Type | Frequency |
| --- | --- |
| Security review | Monthly |
| Dependency review | Monthly |
| Database backup verification | Weekly |
| Supabase health review | Weekly |
| Render deployment log review | Weekly |
| Full system review | Quarterly |

### 4.4 SLA Exclusions

The SLA does not cover:

- Client-side internet outage.
- Supabase platform outage.
- Render platform outage.
- Data loss caused by unauthorized credential sharing.
- Custom features outside the delivered Version 1.0 scope.

---

## 5. Operations Manual

### 5.1 Daily Operations

- Check Render service status.
- Confirm login page and dashboard load.
- Review recent borrow and return activity.
- Check overdue records.
- Review unpaid fines.
- Confirm notifications are visible.
- Monitor application logs for errors.

### 5.2 Weekly Maintenance

- Verify database backup exists.
- Review active and inactive users.
- Review book stock and status.
- Check failed login patterns.
- Generate weekly reports if required.
- Review Supabase database usage.

### 5.3 Monthly Maintenance

- Run Django checks and tests in staging/local environment.
- Review Python package updates.
- Review security settings.
- Confirm `.env` secrets are not exposed.
- Review role assignments.
- Verify recovery process using a safe backup copy.

### 5.4 Backup and Recovery

Backup procedure:

1. Create Supabase PostgreSQL backup.
2. Store backup in secure storage.
3. Record backup date and responsible person.
4. Keep backup access restricted.
5. Test restoration periodically in a non-production environment.

Recovery procedure:

1. Confirm the incident and affected data.
2. Stop risky write operations if possible.
3. Create a current-state backup before restore.
4. Restore the latest valid backup.
5. Run migrations if required.
6. Verify login, dashboard, books, members, borrowing, fines, notifications, and reports.

### 5.5 User Management

- Create users only for authorized library staff and members.
- Assign the lowest role required for the user’s task.
- Disable inactive users.
- Review admin accounts monthly.
- Do not share accounts between staff.

### 5.6 Security Review

Review:

- Supabase Auth users.
- Django local users and roles.
- Render environment variables.
- GitHub repository secrets.
- Database access credentials.
- Backup file access.
- Public deployment URL.

---

## 6. Risk Register

| Risk Type | Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- | --- |
| Technical | Render deployment fails | System unavailable | Medium | Keep rollback plan and previous deployment available |
| Technical | Supabase connection timeout | Users cannot access data | Medium | Use correct pooler/direct connection and SSL settings |
| Technical | Static files fail to load | UI appears broken | Low | Run `collectstatic` and verify WhiteNoise configuration |
| Security | Secret keys exposed | Account or data compromise | Medium | Use `.env`, GitHub secrets, Render env vars, rotate exposed keys |
| Security | Weak account passwords | Unauthorized access | Medium | Use Supabase Auth password policies and disable inactive users |
| Security | Backup file leaked | Data exposure | Medium | Store backups securely and avoid committing backup files |
| Operational | Staff use wrong role | Incorrect access level | Medium | Monthly role review |
| Operational | No recent backup | Recovery difficult | Medium | Weekly backup verification |
| Business | Client expects unsupported features | Scope disagreement | Medium | Confirm Version 1.0 limitations and roadmap |
| Business | Internet outage during demo | Live system unavailable | Low | Prepare screenshots and local fallback demo |

---

## 7. Project Closure Report

### 7.1 Objectives Achieved

| Objective | Status |
| --- | --- |
| Manage books | Achieved |
| Manage categories, authors, and publishers | Achieved |
| Manage members | Achieved |
| Manage users and roles | Achieved |
| Borrow books | Achieved |
| Return books | Achieved |
| Calculate fines | Achieved |
| Store notifications | Achieved |
| Generate reports | Achieved |
| Search and filter books | Achieved |
| Use Supabase PostgreSQL | Prepared and supported |
| Use Supabase Auth | Prepared and supported |
| Deploy on Render | Prepared and documented |
| Preserve 11-table Data Dictionary | Achieved |

### 7.2 Deliverables Completed

- Source code.
- Database models and migrations.
- Templates and static files.
- Supabase configuration guide.
- Render deployment guide.
- Final report.
- User manual.
- Administrator manual.
- Technical documentation.
- Testing documentation.
- Screenshot evidence plan.
- Viva preparation.
- DevOps and CI/CD guide.

### 7.3 Lessons Learned

- Database scope must be confirmed early.
- Supabase Auth should be separated from local authorization.
- Automated tests are important when schema changes.
- Final documentation must match the active implementation.
- Deployment requires careful environment variable management.

### 7.4 Outstanding Issues

- Final live deployment URL must be confirmed by the client/project owner.
- Screenshots should be inserted into the final report.
- Stale or old phase documentation should not be submitted as authoritative.
- Backup files must be handled securely and should not be shared publicly.

### 7.5 Recommendations

- Use Version 1.0 as the stable accepted release.
- Create a separate Version 2.0 plan for reservations, mobile app, barcode/QR, and advanced analytics.
- Keep the production database backed up.
- Review security settings monthly.
- Train staff before live use.

---

## 8. Client Handover Checklist

| Item | Verification | Status |
| --- | --- | --- |
| Source code delivered | Repository or archive provided | Pending |
| Requirements delivered | `requirements.txt` included | Pending |
| Environment template delivered | `.env.example` included, no real secrets | Pending |
| Database documentation delivered | 11-table Data Dictionary included | Pending |
| Migrations delivered | Django migrations included | Pending |
| Static files delivered | CSS, JS, logo, favicon, login image included | Pending |
| Documentation delivered | User, admin, technical, deployment docs included | Pending |
| Deployment verified | Render URL tested | Pending |
| Supabase database verified | Required 11 business tables present | Pending |
| Supabase Auth verified | Login/register tested | Pending |
| Administrator account verified | Admin can log in | Pending |
| Librarian account verified | Librarian workflow tested | Pending |
| Member account verified | Member access tested | Pending |
| Backup verified | Backup procedure confirmed | Pending |
| Training completed | Admin/librarian/member training completed | Pending |
| UAT signed | Client sign-off completed | Pending |

---

## 9. Final Client Sign-Off

Project Name: Enterprise Library Management System  
Version: 1.0.0  
Client / Organization: ______________________________  
Delivery Date: ______________________________  
Deployment URL: ______________________________  

Final decision:

- [ ] Accepted for production/demo use
- [ ] Accepted with minor issues
- [ ] Not accepted

Client Representative:

Name: ______________________________  
Position: ______________________________  
Signature: ______________________________  
Date: ______________________________

Project Representative:

Name: ______________________________  
Position: ______________________________  
Signature: ______________________________  
Date: ______________________________


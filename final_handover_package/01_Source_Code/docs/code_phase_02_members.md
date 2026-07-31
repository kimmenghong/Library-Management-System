# Code Phase 2: Member and Specialized Profile Management

## Scope

This code phase implements the complete `members` Django app and integrates it with authentication, circulation, fines, reservations, notifications, reports, activity auditing, and the REST API.

## App Structure

```text
apps/members/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_alter_member_emergency_contact_phone_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tests.py
├── urls.py
└── views.py

templates/members/
├── member_detail.html
├── member_form.html
├── member_list.html
├── member_status_form.html
└── profile_form.html
```

## Models

- `Member`: one-to-one membership record for an authenticated user
- `StudentProfile`: student ID, academic program, year, semester, and guardian details
- `TeacherProfile`: teacher ID, faculty, department, designation, and office
- `StaffProfile`: staff ID, department, position, and office
- `LibrarianProfile`: librarian ID, employee type, shift, and override authority

## Business Rules

- Member codes are generated as collision-resistant, readable identifiers.
- A user can own only one member record and one compatible specialized profile.
- System roles and member types must agree.
- Institutional IDs are normalized to uppercase and unique case-insensitively in forms.
- Expiry dates cannot precede joined dates.
- Past active memberships are changed to `expired` when saved.
- Student year levels are limited to 1-8 and semesters to 1-3.
- Profile forms only offer eligible members without another specialized profile.
- Existing member records cannot be moved to another user.
- Membership status changes use a dedicated permission-protected workflow.
- REST writes apply the same model-level validation as server-rendered forms.

## URLs

```text
/members/                              Member list and filters
/members/create/                       Create member
/members/<id>/                         Member details and profile
/members/<id>/edit/                    Edit member
/members/<id>/status/                  Change membership status
/members/<id>/<profile-type>/create/   Create the compatible profile
```

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.members
python manage.py test
```

The focused suite covers member codes, dates, active membership, role matching, profile type safety, role assignment, eligible form choices, search, status changes, profile creation, permissions, and API validation.

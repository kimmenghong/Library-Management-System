# Phase 2: Authentication, Users, Roles, Permissions, Members, and Profiles

## Completed Modules

1. Authentication Module
2. User Management Module
3. Role and Permission Module
4. Member Management Module
5. Profile Management Module

## Main Implementation

- Custom `accounts.User` model based on Django `AbstractUser`
- Custom `accounts.Role` model
- Custom `accounts.Permission` model
- Role-based access control helpers through decorators and class-based view mixins
- Member records connected one-to-one with users
- Student, teacher, staff, librarian, and assistant librarian profiles
- Login, logout, password reset, and profile update pages
- Django admin configuration for all Phase 2 models

## RBAC Design

Users receive one role. Roles contain many permissions. Views can protect pages by checking:

```python
request.user.has_role_permission("members.view_member")
```

Superusers automatically pass all role and permission checks.

## Password Reset

The development email backend prints reset links to the console:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

For production, replace it with SMTP settings.

## Next Phase

Phase 3 should add book, author, publisher, category, shelf, location, book copy, ISBN, barcode, and QR code modules.

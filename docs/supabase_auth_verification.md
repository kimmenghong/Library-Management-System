# Supabase Auth Verification

This project uses Supabase Auth for email/password identity and keeps the
lecturer-required `users` table for local profile, role, status, and permission
control.

## Required Environment

```env
USE_SUPABASE_AUTH=True
SUPABASE_PROJECT_REF=aeqcvoglxjlefbkurrys
SUPABASE_URL=https://aeqcvoglxjlefbkurrys.supabase.co
SUPABASE_ANON_KEY=your-real-supabase-anon-public-key
SUPABASE_AUTH_DEFAULT_ROLE=Student
SUPABASE_AUTH_REQUIRE_LOCAL_USER=True
```

Do not commit real secrets. Keep them in `.env`.

## Automated Tests

Run all tests:

```bash
.venv/bin/python manage.py test
```

Run only the Library app tests:

```bash
.venv/bin/python manage.py test apps.library
```

Run Django checks:

```bash
.venv/bin/python manage.py check
```

Check migrations were not changed:

```bash
.venv/bin/python manage.py makemigrations --check --dry-run
```

## Real Supabase Auth Connection Test

Settings-only verification:

```bash
.venv/bin/python manage.py verify_supabase_auth --skip-login
```

Remote login verification:

```bash
.venv/bin/python manage.py verify_supabase_auth --email your-user@example.com
```

The command prompts for the password securely. It verifies:

- Supabase Auth is enabled.
- Supabase URL and anon key are configured.
- Email/password login succeeds through Supabase.
- A matching Django `users` row exists.
- The Django user is active.
- The Django user has a role.

## Common Errors

`USE_SUPABASE_AUTH is False`

Set:

```env
USE_SUPABASE_AUTH=True
```

`SUPABASE_URL and SUPABASE_ANON_KEY are required`

Copy the Project URL and anon public key from Supabase Project Settings > API.

`Invalid login credentials`

Check the email/password in Supabase Auth > Users. Confirm the user has signed up
and the password is correct.

`Email not confirmed`

Confirm the email from the Supabase email link, or disable email confirmation in
Supabase Auth settings for local testing only.

`No matching Django users row exists`

Create or sync a Django `users` row with the same email address. Supabase owns
authentication, but Django owns roles and profile data.

`Matching Django user exists but is inactive`

Set the local Django user `is_active=True` from the admin dashboard or database.

`Matching Django user exists but has no role`

Assign a valid local role in the `roles` table.

`Default role 'Student' does not exist`

Create the `Student` role or change:

```env
SUPABASE_AUTH_DEFAULT_ROLE=Student
```

to a role name that exists in the local `roles` table.

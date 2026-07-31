# GitHub Repository Commands

Release: **v1.0.0**

These commands prepare and publish the project to GitHub. Replace placeholders with your GitHub username and repository name.

## 1. Initialize Repository

```bash
git init
git branch -M main
git status
```

## 2. Stage Files

Recommended for strict 11-table submission:

```bash
git add README.md LICENSE CONTRIBUTING.md CHANGELOG.md CODE_OF_CONDUCT.md SECURITY.md VERSION
git add .gitignore .env.example requirements.txt manage.py
git add config apps/library templates/library static docs/release docs/final_submission_package
```

If you want to include all project files:

```bash
git add .
```

Before committing, check:

```bash
git status
```

Do not commit:

- `.env`
- `.venv/`
- `__pycache__/`
- local SQLite database files unless your lecturer explicitly requests them
- inactive legacy phase apps if strict 11-table submission is required

## 3. Create Commit History

Suggested clean release commit history:

```bash
git commit -m "chore: prepare v1.0.0 release package"
```

Optional fuller history if starting from scratch:

```bash
git add config apps/library templates/library static requirements.txt manage.py .env.example
git commit -m "feat: add corrected 11-table library system"

git add docs README.md
git commit -m "docs: add final submission documentation"

git add LICENSE CONTRIBUTING.md CHANGELOG.md CODE_OF_CONDUCT.md SECURITY.md VERSION docs/release
git commit -m "chore: prepare v1.0.0 release"
```

## 4. Connect To GitHub

Create an empty GitHub repository, then run:

```bash
git remote add origin https://github.com/<your-username>/library-management-system.git
git remote -v
```

## 5. Push Main Branch

```bash
git push -u origin main
```

## 6. Create Release Tag v1.0.0

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 7. Create GitHub Release

On GitHub:

1. Open the repository.
2. Go to Releases.
3. Click Draft a new release.
4. Choose tag `v1.0.0`.
5. Release title: `Library Management System v1.0.0`.
6. Copy release notes from `docs/release/v1.0.0.md`.
7. Publish release.

## 8. Verify Repository

After pushing, confirm:

- README displays correctly.
- License is detected as MIT.
- Release tag `v1.0.0` exists.
- Documentation links work.
- No secret `.env` file is uploaded.
- No virtual environment is uploaded.

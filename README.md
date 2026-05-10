# Library Management & Digital Book Platform

A Django-based library management system with both a user-facing digital library and an admin-facing library operations dashboard.

The project combines traditional library inventory and checkout workflows with user-uploaded digital books, fine payment verification, overdue tracking, encrypted credential support, and admin moderation.

---

## Key Capabilities

- User registration and login via username/password or generated library ID
- Digital book browsing, PDF/EPUB reading, and downloads
- User uploads for digital books with admin verification and banning
- Library book checkout, return, and overdue management
- Fine creation, proof upload, and admin payment verification
- Admin dashboard for user management, transaction tracking, overdue books, and fines
- Encrypted credential storage for overdue library borrower records
- Celery + Redis background tasks for cleanup and overdue tracking
- Legacy library management interface still available under `/resources/`, `/members/`, and `/transactions/`

---

## Project Structure

- `vp/` – Django project configuration
  - `settings.py` – settings, database, static/media, Celery
  - `urls.py` – main route definitions for users, admin, and legacy views
  - `celery.py` – Celery app configuration
- `models/` – main Django application
  - `models.py` – core database models and business objects
  - `views.py` – legacy library resource and member views
  - `user_views.py` – user-facing signup, login, book browsing, uploads, and fines
  - `admin_views.py` – admin-facing dashboards, moderation, user bans, fines, checkout management
  - `forms.py` – all Django forms used across the app
  - `admin.py` – Django admin model registrations and list displays
  - `tasks.py` – Celery background tasks
  - `fine_utils.py` – fine helper utilities
  - `overdue_sync.py` – sync overdue transaction details into overdue/fine records
  - `encryption.py` – privacy and credential encryption helper functions
  - `user_utils.py` – anonymous user/session helpers and overdue cleanup
- `templates/` – HTML templates for user, admin, and legacy views
- `static/` – static assets used by templates
- `media/` – uploaded files, book files, fine proofs, and images
- `db.sqlite3` – default SQLite database file
- `requirements.txt` – Python package dependencies

---

## Important Features and Workflow

### User Flow

- Register a new account at `/user/register/`
- Log in at `/user/login/`
- Browse approved digital books via `/user/books/`
- View book detail pages, read PDFs or EPUBs, and download files
- Upload digital books for admin verification at `/user/upload/`
- Leave reviews on digital books and borrowed library books
- Borrow library books, submit return requests, and pay overdue fines

### Admin Flow

- Admin login at `/admin/` or `/admin/login/`
- Admin dashboard at `/admin/dashboard/`
- Approve or reject digital uploads at `/admin/user-books/`
- Manage library users and bans at `/admin/users/`
- Track overdue books at `/admin/overdue-books/`
- Manage fines and verify payments at `/admin/fines/`
- Review and approve/reject manual checkout requests at `/admin/checkouts/`

### Fine Payment Verification

- Fines are created for overdue borrowings or imposed manually
- Users upload proof of payment at `/user/fines/pay/`
- Uploaded proofs are stored under `media/fine_proofs/%Y/%m/%d/`
- Admins verify payments and update fine status at `/admin/fines/`

### Overdue Tracking and Credential Storage

- Overdue transactions create or update `OverdueBook` and `Fine` records
- Overdue records store both display-friendly borrower data and encrypted credential fields
- Encryption keys are configured via `ENCRYPTION_KEY` in environment variables

### User-Uploaded Digital Book Moderation

- Uploaded books are stored in `UserBook`
- Admins verify or ban uploads before they appear in the public library
- Reviews, ratings, views, and download counts are tracked

--

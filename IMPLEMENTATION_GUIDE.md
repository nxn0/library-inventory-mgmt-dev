# Library Inventory Management System - Implementation Guide

## 📋 Project Overview

This is a comprehensive library management system with **two distinct interfaces**:

1. **Admin Side**: Manage physical library stock, members, checkouts, and administrative tasks
2. **User Side**: Browse/upload digital books, borrow physical books, leave reviews, and manage reading

## ✅ What Has Been Implemented

### 1. **Database Models** ✓
All new models have been created in `models/models.py`:

- **AnonymousUser**: Anonymous user sessions with fingerprint tracking
- **UserAuthentication**: Encrypted user credentials (LibraryID or Name+Phone+Credentials)
- **UserBook**: Digital books uploaded by users (PDF/EPUB)
- **UserReview**: User reviews and ratings for digital books
- **UserBan**: User ban management with temporary/permanent options
- **Fine**: Fine tracking for overdue library books
- **OverdueBook**: Separate table for overdue books (unencrypted for admin viewing)

### 2. **Encryption Utilities** ✓
`models/encryption.py` - Implements privacy-first encryption:
- AES-256 reversible encryption using Fernet
- LibraryID/StudentID encryption and decryption
- Combined encryption for Name+Phone+Credentials
- Browser fingerprint hashing for anonymous user identification

### 3. **User Authentication & Session Management** ✓
`models/user_utils.py` - Core utilities:
- **UserSessionManager**: 
  - Anonymous user creation and tracking
  - Browser fingerprinting for session identification
  - Authentication with multiple methods (LibraryID or Credentials)
  - Auto-ban tracking
- **OverdueTracker**:
  - Overdue book detection (15 days)
  - Auto-blacklisting after 30 days
  - Expiration cleanup tasks
  - Ban expiration management

### 4. **User-Side Views** ✓
`models/user_views.py` - Complete user interface:

**Authentication:**
- `user_login()`: Privacy-first login with two authentication methods
- `user_logout()`: Session cleanup
- `user_home()`: Public landing page
- `user_dashboard()`: Personalized user dashboard

**Book Browsing & Reading:**
- `user_browse_books()`: Search, filter, sort digital books
- `user_book_detail()`: View book details and reviews
- `user_read_book_pdf()`: In-browser PDF viewer
- `user_read_book_epub()`: In-browser EPUB reader
- `user_download_book()`: Download functionality

**Book Management:**
- `user_upload_book()`: Upload PDF/EPUB books
- `user_manage_uploads()`: Manage uploaded books

**Reviews & Ratings:**
- `user_leave_review()`: Post reviews with ratings

**Library Borrowing:**
- `user_borrow_library_book()`: Browse library books
- `user_checkout_book()`: Checkout physical books
- `user_return_book()`: Return borrowed books

### 5. **Admin-Side Management Views** ✓
`models/admin_views.py` - Comprehensive admin interface:

**Digital Book Management:**
- `admin_user_books()`: List and filter all digital books
- `admin_verify_book()`: Verify user-uploaded books
- `admin_ban_book()`: Ban inappropriate books
- `admin_delete_book()`: Remove books

**User Management:**
- `admin_manage_users()`: List all users
- `admin_ban_user()`: Ban users temporarily or permanently
- `admin_unban_user()`: Lift user bans
- `admin_delete_user()`: Delete accounts

**Fine Management:**
- `admin_manage_fines()`: View and filter fines
- `admin_impose_fine()`: Impose fines on members
- `admin_mark_fine_paid()`: Track fine payments

**Overdue Tracking:**
- `admin_overdue_books()`: View all overdue books
- `admin_mark_book_recovered()`: Mark books as recovered

**Checkout Tracking:**
- `admin_checkout_tracking()`: View transaction history
- `admin_manual_checkout()`: Create manual checkouts

**Dashboard:**
- `admin_dashboard()`: Overview statistics and recent activity

### 6. **Forms** ✓
`models/forms.py` - All forms for admin and user sides:

**Admin Forms:**
- ResourceForm, CategoryForm, MemberForm, CheckoutForm, StockLogForm
- FineForm, UserBanForm

**User Forms:**
- UserLoginForm, UserBookUploadForm, UserReviewForm

### 7. **URL Routing** ✓
`vp/urls.py` - Complete URL configuration:

- User-side URLs: `/user/`, `/user/login/`, `/user/books/`, etc.
- Admin new URLs: `/admin/dashboard/`, `/admin/users/`, `/admin/fines/`, etc.
- Existing admin URLs preserved

### 8. **Django Admin Integration** ✓
`models/admin.py` - Registered all new models in Django admin:
- AnonymousUserAdmin
- UserAuthenticationAdmin
- UserBookAdmin
- UserReviewAdmin
- UserBanAdmin
- FineAdmin
- OverdueBookAdmin

### 9. **Background Tasks** ✓
`models/tasks.py` - Celery tasks for background operations:
- `cleanup_expired_sessions()`: Delete 30+ day inactive users
- `track_overdue_books()`: Move old overdue books to permanent table
- `cleanup_expired_bans()`: Remove expired temporary bans

### 10. **Templates** ✓
Bootstrap 5-based responsive templates:

- `templates/user/base.html`: Base template with navigation
- `templates/user/login.html`: Two-method authentication UI
- `templates/user/home.html`: Landing page with featured books
- `templates/user/browse_books.html`: Book browsing with search/filter
- `templates/user/book_detail.html`: Book details and reviews
- `templates/user/upload_book.html`: Book upload form

### 11. **Updated Requirements** ✓
`requirements.txt` - Added dependencies:
- cryptography (for AES encryption)
- PyPDF2 (PDF handling)
- ebooklib (EPUB support)
- celery & redis (background tasks)

## 🔄 What Still Needs to be Done

### 1. **Run Database Migrations**
```bash
cd /home/nandana/vp
python manage.py makemigrations models
python manage.py migrate
```

### 2. **PDF/EPUB Reader Templates**
Create in-browser readers:
```
templates/user/read_pdf.html    # PDF.js integration
templates/user/read_epub.html   # EPUB.js integration
```

### 3. **Additional User Templates**
```
templates/user/dashboard.html           # User dashboard
templates/user/manage_uploads.html      # Manage uploaded books
templates/user/borrow_library_books.html # Browse library books
templates/user/return_book.html         # Return interface
```

### 4. **Admin Templates**
```
templates/admin/dashboard.html         # Admin overview
templates/admin/user_books.html        # Digital book management
templates/admin/manage_users.html      # User management
templates/admin/manage_fines.html      # Fine management
templates/admin/overdue_books.html     # Overdue tracking
templates/admin/checkout_tracking.html # Checkout history
templates/admin/*.html                 # Other admin pages
```

### 5. **Celery Configuration**
- Create `vp/celery.py` for Celery setup
- Configure celery beat for periodic tasks
- Add to `vp/settings.py`:
  ```python
  CELERY_BROKER_URL = 'redis://localhost:6379'
  CELERY_RESULT_BACKEND = 'redis://localhost:6379'
  ```

### 6. **Settings Updates** (`vp/settings.py`)
```python
# Add encryption key for privacy
ENCRYPTION_KEY = env('ENCRYPTION_KEY', 'your-secret-key')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 2592000  # 30 days

# CORS and security settings if needed
```

### 7. **Middleware for Anonymous Users**
Create middleware to auto-create anonymous users on every page visit.

### 8. **API Endpoints** (Optional)
- AJAX endpoints for AJAX form submissions
- REST API for mobile app integration

### 9. **Static Files**
Collect static files:
```bash
python manage.py collectstatic
```

### 10. **Testing**
- Unit tests for encryption utilities
- Integration tests for views
- Test overdue tracking logic

### 11. **Documentation**
- API documentation
- User guide
- Admin guide

## 🚀 Quick Start Guide

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Create Migrations**
```bash
python manage.py makemigrations models
python manage.py migrate
```

### 3. **Create Superuser**
```bash
python manage.py createsuperuser
```

### 4. **Run Development Server**
```bash
python manage.py runserver
```

### 5. **Access the Application**
- Admin Dashboard: `http://localhost:8000/`
- User Home: `http://localhost:8000/user/`
- Django Admin: `http://localhost:8000/admin/`

## 🔐 Privacy & Security Features

1. **Anonymous Sessions**: Users get anonymous IDs on first visit
2. **AES-256 Encryption**: All sensitive data is encrypted
3. **Fingerprint Tracking**: Browser fingerprinting prevents session hijacking
4. **Auto-Cleanup**: Inactive sessions deleted after 30 days
5. **Encrypted Overdue Tracking**: Separate database for overdue books
6. **User Banning**: Multiple ban types (temporary/permanent)

## 📊 Database Structure

### Key Tables
- `AnonymousUser`: Anonymous user sessions
- `UserAuthentication`: Encrypted credentials
- `UserBook`: Digital books (PDF/EPUB)
- `UserReview`: Reviews and ratings
- `OverdueBook`: Overdue tracking (unencrypted)
- `UserBan`: Ban management
- `Fine`: Fine tracking

## 🛠️ Configuration

### Required Settings
```python
# Encryption
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = 'media'

# Session
SESSION_COOKIE_AGE = 2592000  # 30 days
```

### Optional Celery Tasks
Add to `celery_config.py`:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup_sessions': {
        'task': 'models.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'track_overdue': {
        'task': 'models.tasks.track_overdue_books',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'cleanup_bans': {
        'task': 'models.tasks.cleanup_expired_bans',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## 📝 File Structure Summary

```
/home/nandana/vp/
├── models/
│   ├── models.py           # ✓ All database models
│   ├── views.py            # Existing admin views
│   ├── user_views.py       # ✓ User-side views
│   ├── admin_views.py      # ✓ Admin-side views
│   ├── forms.py            # ✓ All forms
│   ├── encryption.py       # ✓ Encryption utilities
│   ├── user_utils.py       # ✓ User session management
│   ├── tasks.py            # ✓ Celery tasks
│   └── admin.py            # ✓ Django admin registration
├── templates/
│   ├── user/
│   │   ├── base.html       # ✓ Base template
│   │   ├── login.html      # ✓ Login template
│   │   ├── home.html       # ✓ Home template
│   │   ├── browse_books.html # ✓ Browse template
│   │   ├── book_detail.html# ✓ Book detail template
│   │   ├── upload_book.html# ✓ Upload template
│   │   └── ... (more templates TBD)
│   └── admin/
│       └── ... (TBD)
├── vp/
│   ├── settings.py         # Needs updates
│   ├── urls.py             # ✓ Updated with all URLs
│   └── ...
├── manage.py
├── requirements.txt        # ✓ Updated with new packages
└── db.sqlite3
```

## ⚠️ Important Notes

1. **JavaScript Libraries Needed**:
   - PDF.js (for PDF reading)
   - EPUB.js (for EPUB reading)

2. **Media Storage**:
   - PDFs and EPUBs will be stored in `/media/user_books/`
   - Ensure proper permissions on this directory

3. **Encryption Keys**:
   - Store `ENCRYPTION_KEY` in environment variables
   - Never hardcode in production

4. **Performance**:
   - Consider adding Redis for caching
   - Use database indexes (already added in models)

5. **Testing**:
   - Test encryption/decryption thoroughly
   - Test overdue detection logic
   - Verify permission controls

## 🎯 Next Steps

1. Run migrations
2. Create templates for PDF/EPUB readers
3. Create admin interface templates
4. Set up Celery with Redis
5. Test the complete workflow
6. Deploy to production

---

**Status**: Core implementation complete. Ready for template creation and testing.

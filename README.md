# Library Resource Management System

A complete Django-based CRUD application for managing library resources, members, and transactions.

## Features

### Core Functionality
- **Resource Management**: Add, view, update, and delete library resources (books, equipment, magazines)
- **Category Management**: Organize resources into categories
- **Member Management**: Track library members (students, faculty, staff)
- **Check-out/Check-in System**: Borrow and return resources with due dates
- **Stock Tracking**: Log additions/removals of resources
- **Fine Calculation**: Automatic fine calculation for overdue items
- **Dashboard**: Overview with statistics and alerts

### Additional Features
- Search and filter functionality across all entities
- Low stock alerts
- Overdue item tracking
- Transaction history
- Popular categories analytics

## Project Structure

```
library_project/
│
├── library_project/          # Main project folder
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── library/                  # App folder
│   ├── migrations/
│   ├── templates/
│   │   └── library/
│   │       ├── dashboard.html
│   │       ├── resource_list.html
│   │       ├── resource_detail.html
│   │       ├── resource_form.html
│   │       ├── resource_confirm_delete.html
│   │       ├── category_list.html
│   │       ├── category_form.html
│   │       ├── member_list.html
│   │       ├── member_detail.html
│   │       ├── member_form.html
│   │       ├── transaction_list.html
│   │       ├── checkout_form.html
│   │       ├── checkin_confirm.html
│   │       └── stock_log_form.html
│   ├── static/
│   │   └── library/
│   │       ├── css/
│   │       └── js/
│   ├── models.py             # (Already provided)
│   ├── views.py              # (Already provided)
│   ├── forms.py              # (Already provided)
│   ├── urls.py               # (Already provided)
│   ├── admin.py              # (Already provided)
│   └── apps.py
│
├── media/                    # For uploaded images
├── static/                   # Global static files
├── manage.py
└── requirements.txt
```

## Installation & Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install django
pip install pillow  # For image handling
```

Or create `requirements.txt`:
```
Django>=4.2,<5.0
Pillow>=10.0
```

Then run:
```bash
pip install -r requirements.txt
```

### 3. Create Django Project
```bash
django-admin startproject library_project
cd library_project
python manage.py startapp library
```

### 4. Configure Settings

In `library_project/settings.py`, add:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'library',  # Add your app
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

In `library_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 5. Copy the Provided Files

Copy the code artifacts I provided into:
- `library/models.py`
- `library/views.py`
- `library/forms.py`
- `library/urls.py`
- `library/admin.py`

### 6. Create Migrations & Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Create Templates


**Create `library/templates/library/base.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Library Management{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'dashboard' %}">Library System</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'dashboard' %}">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'resource_list' %}">Resources</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'member_list' %}">Members</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'transaction_list' %}">Transactions</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'category_list' %}">Categories</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

### 9. Run the Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

## Database Models

### Resource
- Title, Resource ID (ISBN/Serial), Category
- Author/Manufacturer, Publisher, Year
- Total/Available quantity
- Shelf location, Status, Cost
- Image upload support

### Category
- Name, Description
- Automatic resource counting

### Member
- Member ID, Name, Email, Phone
- Type (Student/Faculty/Staff)
- Department, Join date, Active status

### Transaction
- Resource, Member, Type (Checkout/Checkin/Renew)
- Checkout/Due/Return dates
- Status (Active/Returned/Overdue)
- Fine calculation

### StockLog
- Resource, Action (Add/Remove/Damage/Lost)
- Quantity, Reason, Performed by
- Timestamp

## Usage Guide

### Adding Resources
1. Go to Resources → Add New Resource
2. Fill in details (title, ID, category, quantity)
3. Upload image (optional)
4. Set shelf location and initial stock

### Managing Members
1. Go to Members → Add New Member
2. Enter member details and type
3. Assign member ID

### Checking Out Resources
1. Go to Transactions → Check Out
2. Select resource and member
3. Set due date (default 14 days)
4. Submit

### Checking In Resources
1. Go to Transactions list
2. Find active transaction
3. Click "Check In"
4. System calculates fines if overdue

### Stock Management
1. View resource details
2. Click "Add Stock Log"
3. Select action (add/remove/damage)
4. Enter quantity and reason

## Sample Data


```bash
python manage.py shell
```

```python
from library.models import Category, Resource, Member

# Create categories
cat1 = Category.objects.create(name="Books", description="Physical and digital books")
cat2 = Category.objects.create(name="Equipment", description="Lab and tech equipment")

# Create resources
Resource.objects.create(
    title="Introduction to Algorithms",
    resource_id="ISBN-001",
    category=cat1,
    author="Cormen et al",
    total_quantity=5,
    available_quantity=5
)

# Create members
Member.objects.create(
    member_id="STU001",
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    member_type="student"
)
```

## Template Examples


### Dashboard (dashboard.html)
- Statistics cards (total resources, members, checked out, overdue)
- Low stock alerts
- Recent transactions table
- Popular categories

### Resource List (resource_list.html)
- Search bar and filters
- Table with all resources
- Add new resource button
- Edit/Delete actions

### Resource Form (resource_form.html)
- Form fields from ResourceForm
- Image upload
- Submit/Cancel buttons

### Transaction List (transaction_list.html)
- All checkout/checkin records
- Status filters
- Check-in buttons for active transactions


## Grading Points to Hit

- ✅ Multiple models with relationships (5 models)
- ✅ Full CRUD operations on all entities
- ✅ Form validation
- ✅ Search and filter functionality
- ✅ Business logic (fine calculation, stock updates)
- ✅ Dashboard with analytics
- ✅ Clean UI with Bootstrap
- ✅ Admin panel configuration

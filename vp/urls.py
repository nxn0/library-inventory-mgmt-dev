from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from models import views, user_views, admin_views

urlpatterns = [
    # Django Admin Panel
    path('admin-panel/', admin.site.urls),
    
    # ========== DEFAULT: USER SIDE HOME PAGE ==========
    path('', user_views.user_home, name='user_home'),
    
    # ========== USER SIDE ==========
    # Authentication
    path('user/login/', user_views.user_login, name='user_login'),
    path('user/register/', user_views.user_register, name='user_register'),
    path('user/logout/', user_views.user_logout, name='user_logout'),
    path('user/dashboard/', user_views.user_dashboard, name='user_dashboard'),
    
    # Book browsing & reading
    path('user/books/', user_views.user_browse_books, name='user_browse_books'),
    path('user/books/<int:book_id>/', user_views.user_book_detail, name='user_book_detail'),
    path('user/books/<int:book_id>/read-pdf/', user_views.user_read_book_pdf, name='user_read_pdf'),
    path('user/books/<int:book_id>/read-epub/', user_views.user_read_book_epub, name='user_read_epub'),
    path('user/books/<int:book_id>/download/', user_views.user_download_book, name='user_download_book'),
    path('user/resources/<int:resource_id>/', user_views.user_resource_detail, name='user_resource_detail'),
    
    # Book upload & management
    path('user/upload/', user_views.user_upload_book, name='user_upload_book'),
    path('user/my-uploads/', user_views.user_manage_uploads, name='user_manage_uploads'),
    
    # Reviews & ratings
    path('user/books/<int:book_id>/review/', user_views.user_leave_review, name='user_leave_review'),
    
    # Library book borrowing
    path('user/borrow/', user_views.user_borrow_library_book, name='user_borrow_library_book'),
    path('user/checkout/<int:resource_id>/', user_views.user_checkout_book, name='user_checkout_book'),
    path('user/return/', user_views.user_return_book, name='user_return_book'),
    
    # ========== ADMIN PANEL (PROTECTED) ==========
    # Admin authentication & dashboard
    path('admin/', admin_views.admin_login, name='admin_login'),
    path('admin/login/', admin_views.admin_login, name='admin_login_alt'),
    path('admin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Digital book management
    path('admin/user-books/', admin_views.admin_user_books, name='admin_user_books'),
    path('admin/user-books/<int:book_id>/verify/', admin_views.admin_verify_book, name='admin_verify_book'),
    path('admin/user-books/<int:book_id>/ban/', admin_views.admin_ban_book, name='admin_ban_book'),
    path('admin/user-books/<int:book_id>/delete/', admin_views.admin_delete_book, name='admin_delete_book'),
    
    # User management & banning
    path('admin/users/', admin_views.admin_manage_users, name='admin_manage_users'),
    path('admin/users/<int:user_auth_id>/ban/', admin_views.admin_ban_user, name='admin_ban_user'),
    path('admin/users/<int:user_auth_id>/unban/', admin_views.admin_unban_user, name='admin_unban_user'),
    path('admin/users/<int:user_auth_id>/delete/', admin_views.admin_delete_user, name='admin_delete_user'),
    
    # Fines management
    path('admin/fines/', admin_views.admin_manage_fines, name='admin_manage_fines'),
    path('admin/fines/impose/<int:member_id>/', admin_views.admin_impose_fine, name='admin_impose_fine'),
    path('admin/fines/<int:fine_id>/mark-paid/', admin_views.admin_mark_fine_paid, name='admin_mark_fine_paid'),
    
    # Overdue books tracking
    path('admin/overdue-books/', admin_views.admin_overdue_books, name='admin_overdue_books'),
    path('admin/overdue-books/<int:overdue_book_id>/recovered/', admin_views.admin_mark_book_recovered, name='admin_mark_book_recovered'),
    
    # Checkout tracking
    path('admin/checkouts/', admin_views.admin_checkout_tracking, name='admin_checkout_tracking'),
    path('admin/checkouts/manual/', admin_views.admin_manual_checkout, name='admin_manual_checkout'),
    
    # ========== OLD ADMIN SIDE (LIBRARY MANAGEMENT) - REDIRECT TO ADMIN LOGIN ==========
    # Resources
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('resources/create/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/edit/', views.resource_edit, name='resource_edit'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),

    # User uploaded digital books management in legacy UI
    path('resources/user-books/<int:book_id>/edit/', views.resource_edit_user_book, name='resource_edit_user_book'),
    path('resources/user-books/<int:book_id>/verify/', views.resource_verify_user_book, name='resource_verify_user_book'),
    path('resources/user-books/<int:book_id>/ban/', views.resource_ban_user_book, name='resource_ban_user_book'),
    path('resources/user-books/<int:book_id>/delete/', views.resource_delete_user_book, name='resource_delete_user_book'),
    
    # Members
    path('members/', views.member_list, name='member_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/register/<str:token>/', views.member_register, name='member_register'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    
    # Transactions
    path('checkout/', views.checkout_create, name='checkout_create'),
    path('return/', views.return_resource, name='return_resource'),
    path('transactions/', views.transaction_list, name='transaction_list'),

    # User uploaded book management in legacy resources
    path('resources/user-books/<int:book_id>/view/', views.resource_view_user_book, name='resource_view_user_book'),
    path('resources/user-books/<int:book_id>/edit/', views.resource_edit_user_book, name='resource_edit_user_book'),
    path('resources/user-books/<int:book_id>/verify/', views.resource_verify_user_book, name='resource_verify_user_book'),
    path('resources/user-books/<int:book_id>/ban/', views.resource_ban_user_book, name='resource_ban_user_book'),
    path('resources/user-books/<int:book_id>/delete/', views.resource_delete_user_book, name='resource_delete_user_book'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

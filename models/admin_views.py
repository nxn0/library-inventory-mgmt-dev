"""
Admin-side management views for user-side application.
Includes digital book management, user banning, fines, and overdue tracking.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from datetime import timedelta

from .models import (
    UserBook, UserAuthentication, UserBan, Fine, OverdueBook,
    AnonymousUser, Transaction, Resource, Member
)
from .forms import FineForm, UserBanForm
from .user_utils import OverdueTracker
from .encryption import PrivacyEncryption
from .views import dashboard as inventory_dashboard


# ========== ADMIN AUTHENTICATION ==========

def admin_is_authenticated(request):
    """Check if user is authenticated as admin"""
    return (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)) or request.session.get('is_custom_admin', False)


def admin_login(request):
    """Admin login page"""
    if admin_is_authenticated(request):
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        # Legacy fixed credentials
        if username == 'admin' and password == '12345':
            request.session['is_custom_admin'] = True
            messages.success(request, 'Welcome, admin! Redirecting to classic inventory dashboard.')
            return redirect('admin_dashboard')

        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'admin/login.html', {})


def admin_logout(request):
    """Admin logout"""
    if request.session.get('is_custom_admin'):
        request.session.pop('is_custom_admin', None)

    if request.user.is_authenticated:
        logout(request)

    messages.success(request, 'You have been logged out.')
    return redirect('user_home')


def admin_required(view_func):
    """Decorator to check if user is authenticated as admin (staff/superuser)"""
    def wrapper(request, *args, **kwargs):
        if not admin_is_authenticated(request):
            messages.error(request, 'Admin access required. Please login.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ========== DIGITAL BOOK MANAGEMENT ==========

@admin_required
def admin_user_books(request):
    """Manage digital books uploaded by users"""
    books = UserBook.objects.all().annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'unverified':
        books = books.filter(is_verified=False)
    elif status_filter == 'banned':
        books = books.filter(is_banned=True)
    elif status_filter == 'verified':
        books = books.filter(is_verified=True, is_banned=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(uploaded_by_user__fingerprint_hash__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin/user_books.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_verify_book(request, book_id):
    """Verify a digital book"""
    book = get_object_or_404(UserBook, id=book_id)
    book.is_verified = True
    book.save(update_fields=['is_verified'])
    
    messages.success(request, f'Book "{book.title}" verified!')
    return redirect('admin_user_books')


@admin_required
@require_http_methods(["GET", "POST"])
def admin_ban_book(request, book_id):
    """Ban a digital book"""
    book = get_object_or_404(UserBook, id=book_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        book.is_banned = True
        book.ban_reason = reason
        book.save(update_fields=['is_banned', 'ban_reason'])
        
        messages.success(request, f'Book "{book.title}" has been banned.')
        return redirect('admin_user_books')
    
    context = {'book': book}
    return render(request, 'admin/ban_book.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_delete_book(request, book_id):
    """Delete a digital book"""
    book = get_object_or_404(UserBook, id=book_id)
    title = book.title
    
    # Delete the file
    if book.file:
        book.file.delete()
    if book.cover_image:
        book.cover_image.delete()
    
    book.delete()
    messages.success(request, f'Book "{title}" has been deleted.')
    return redirect('admin_user_books')


# ========== USER MANAGEMENT & BANNING ==========

@admin_required
def admin_manage_users(request):
    """Manage user accounts"""
    users = UserAuthentication.objects.all().order_by('-created_at')
    
    # Filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'banned':
        users = users.filter(is_banned=True)
    elif status_filter == 'active':
        users = users.filter(is_active=True, is_banned=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(encrypted_library_id__icontains=search_query) |
            Q(member__member_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin/manage_users.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def admin_ban_user(request, user_auth_id):
    """Ban a user"""
    user_auth = get_object_or_404(UserAuthentication, id=user_auth_id)
    
    # Check if already banned
    if user_auth.ban and user_auth.ban.is_active:
        messages.warning(request, 'User is already banned.')
        return redirect('admin_manage_users')
    
    if request.method == 'POST':
        form = UserBanForm(request.POST)
        if form.is_valid():
            ban = form.save(commit=False)
            ban.user_auth = user_auth
            ban.banned_by = request.user.username if request.user else 'Admin'
            ban.save()
            
            user_auth.is_banned = True
            user_auth.ban_date = timezone.now()
            user_auth.save(update_fields=['is_banned', 'ban_date'])
            
            messages.success(request, f'User has been banned: {ban.reason}')
            return redirect('admin_manage_users')
    else:
        form = UserBanForm()
    
    context = {'user_auth': user_auth, 'form': form}
    return render(request, 'admin/ban_user.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_unban_user(request, user_auth_id):
    """Unban a user"""
    user_auth = get_object_or_404(UserAuthentication, id=user_auth_id)
    
    if user_auth.ban:
        user_auth.ban.delete()
    
    user_auth.is_banned = False
    user_auth.save(update_fields=['is_banned'])
    
    messages.success(request, 'User has been unbanned.')
    return redirect('admin_manage_users')


@admin_required
@require_http_methods(["POST"])
def admin_delete_user(request, user_auth_id):
    """Delete a user account"""
    user_auth = get_object_or_404(UserAuthentication, id=user_auth_id)
    user_auth.delete()
    
    messages.success(request, 'User account has been deleted.')
    return redirect('admin_manage_users')


# ========== FINES MANAGEMENT ==========

@admin_required
def admin_manage_fines(request):
    """Manage member fines"""
    fines = Fine.objects.select_related('member', 'resource').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'unpaid':
        fines = fines.filter(is_paid=False)
    elif status_filter == 'paid':
        fines = fines.filter(is_paid=True)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        fines = fines.filter(
            Q(member__member_id__icontains=search_query) |
            Q(member__first_name__icontains=search_query) |
            Q(member__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(fines, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_unpaid = Fine.objects.filter(is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_unpaid': total_unpaid,
    }
    return render(request, 'admin/manage_fines.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def admin_impose_fine(request, member_id):
    """Impose a fine on a member"""
    member = get_object_or_404(Member, id=member_id)
    
    if request.method == 'POST':
        form = FineForm(request.POST)
        if form.is_valid():
            fine = form.save()
            messages.success(request, f'Fine of Rs. {fine.amount} imposed on {member.full_name}')
            return redirect('admin_manage_fines')
    else:
        form = FineForm(initial={'member': member})
    
    context = {'member': member, 'form': form}
    return render(request, 'admin/impose_fine.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_mark_fine_paid(request, fine_id):
    """Mark a fine as paid"""
    fine = get_object_or_404(Fine, id=fine_id)
    fine.is_paid = True
    fine.paid_date = timezone.now()
    fine.paid_amount = fine.amount
    fine.save()
    
    messages.success(request, f'Fine marked as paid.')
    return redirect('admin_manage_fines')


# ========== OVERDUE BOOKS TRACKING ==========

@admin_required
def admin_overdue_books(request):
    """View overdue books and users"""
    overdue_books = OverdueBook.objects.filter(is_recovered=False).order_by('-days_overdue')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        overdue_books = overdue_books.filter(
            Q(user_identifier__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(book_title__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(overdue_books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_overdue = overdue_books.count()
    total_days_overdue = overdue_books.aggregate(Sum('days_overdue'))['days_overdue__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_overdue': total_overdue,
        'total_days_overdue': total_days_overdue,
    }
    return render(request, 'admin/overdue_books.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_mark_book_recovered(request, overdue_book_id):
    """Mark an overdue book as recovered"""
    overdue_book = get_object_or_404(OverdueBook, id=overdue_book_id)
    overdue_book.is_recovered = True
    overdue_book.recovery_date = timezone.now()
    overdue_book.save()
    
    messages.success(request, f'Book "{overdue_book.book_title}" marked as recovered.')
    return redirect('admin_overdue_books')


@admin_required
def admin_checkout_tracking(request):
    """Manual checkout tracking for library books"""
    transactions = Transaction.objects.select_related('member', 'resource').order_by('-checkout_date')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            Q(member__member_id__icontains=search_query) |
            Q(resource__title__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin/checkout_tracking.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_manual_checkout(request):
    """Create a manual checkout"""
    member_id = request.POST.get('member_id')
    resource_id = request.POST.get('resource_id')
    due_days = int(request.POST.get('due_days', 15))
    
    try:
        member = Member.objects.get(id=member_id)
        resource = Resource.objects.get(id=resource_id)
    except (Member.DoesNotExist, Resource.DoesNotExist):
        messages.error(request, 'Invalid member or resource.')
        return redirect('admin_checkout_tracking')
    
    due_date = timezone.now().date() + timedelta(days=due_days)
    transaction = Transaction.objects.create(
        member=member,
        resource=resource,
        due_date=due_date,
        status='active'
    )
    
    resource.available_quantity -= 1
    resource.save(update_fields=['available_quantity'])
    
    messages.success(request, f'Checkout recorded for {member.full_name}')
    return redirect('admin_checkout_tracking')


# ========== ADMIN DASHBOARD ==========

@admin_required
def admin_dashboard(request):
    """Admin dashboard for user-side management"""
    if request.session.get('is_custom_admin', False):
        # Legacy inventory dashboard from previous system
        return inventory_dashboard(request)

    # Statistics
    total_users = UserAuthentication.objects.count()
    banned_users = UserAuthentication.objects.filter(is_banned=True).count()
    total_books = UserBook.objects.count()
    unverified_books = UserBook.objects.filter(is_verified=False).count()
    banned_books = UserBook.objects.filter(is_banned=True).count()
    
    # Overdue books
    overdue_books = OverdueBook.objects.filter(is_recovered=False).count()
    
    # Unpaid fines
    unpaid_fines_amount = Fine.objects.filter(is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    unpaid_fines_count = Fine.objects.filter(is_paid=False).count()
    
    # Recent activity
    recent_uploads = UserBook.objects.order_by('-created_at')[:5]
    recent_bans = UserBan.objects.order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'banned_users': banned_users,
        'total_books': total_books,
        'unverified_books': unverified_books,
        'banned_books': banned_books,
        'overdue_books': overdue_books,
        'unpaid_fines_amount': unpaid_fines_amount,
        'unpaid_fines_count': unpaid_fines_count,
        'recent_uploads': recent_uploads,
        'recent_bans': recent_bans,
    }
    return render(request, 'admin/dashboard.html', context)

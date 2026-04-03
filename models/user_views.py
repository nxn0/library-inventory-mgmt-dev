"""
User-facing views for the library system.
Includes authentication, book browsing, uploads, reading, and reviews.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import (
    UserBook, UserReview, AnonymousUser, UserAuthentication, 
    Resource, Transaction, Member, UserBan, Fine
)
from .forms import (
    UserLoginForm, UserBookUploadForm, UserReviewForm
)
from .user_utils import UserSessionManager
from .encryption import PrivacyEncryption


# ========== AUTHENTICATION VIEWS ==========

@require_http_methods(["GET", "POST"])
@csrf_protect
def user_login(request):
    """User login page with privacy-first approach"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login_method = form.cleaned_data.get('login_method')
            
            # Authentication methods
            if login_method in ['library_id', 'student_id']:
                user_id = form.cleaned_data.get('library_id')
                username = form.cleaned_data.get('username')
                user_auth = UserSessionManager.authenticate_with_library_id(user_id, username=username)
                if user_auth and not user_auth.username:
                    user_auth.username = username or UserSessionManager.generate_unique_username(base=f"user{user_id[:3]}")
                    user_auth.save(update_fields=['username'])

            elif login_method == 'username':
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')

                # Admin fallback route
                if username == 'admin' and password == '12345':
                    request.session['is_custom_admin'] = True
                    messages.success(request, 'Welcome admin! Redirecting to inventory management dashboard.')
                    return redirect('admin_dashboard')

                user_auth = UserSessionManager.authenticate_with_username(username, password)
                if not user_auth:
                    messages.error(request, 'Invalid username/password or banned user.')
                    return redirect('user_login')

            else:  # credentials method
                name = form.cleaned_data.get('user_name')
                phone = form.cleaned_data.get('user_phone')
                password = form.cleaned_data.get('credentials')
                user_auth = UserSessionManager.authenticate_with_credentials(name, phone, password)
                if user_auth and not user_auth.username:
                    user_auth.username = UserSessionManager.generate_unique_username(base=f"user{phone[-3:] if phone else 'x'}")
                    user_auth.save(update_fields=['username'])
            
            if user_auth is None:
                messages.error(request, 'Invalid credentials or your account is banned.')
                return redirect('user_login')
            
            # Store user authentication in session
            request.session['user_auth_id'] = user_auth.id
            request.session['user_auth_method'] = user_auth.auth_method
            
            messages.success(request, f'Welcome! Logged in as {user_auth.auth_method}.')
            return redirect('user_dashboard')
    else:
        form = UserLoginForm()
    
    context = {'form': form}
    return render(request, 'user/login.html', context)


@require_http_methods(["GET", "POST"])
@csrf_protect
def user_register(request):
    """User self-register with library/student ID and auto-generated username + password"""
    if request.method == 'POST':
        library_id = request.POST.get('library_id', '').strip()
        username = request.POST.get('username', '').strip() or None
        password = request.POST.get('password', '').strip() or None

        if not library_id:
            messages.error(request, 'Please provide your Library/Student ID.')
            return redirect('user_register')

        if not password:
            messages.error(request, 'Please set a password for username login.')
            return redirect('user_register')

        user_auth = UserSessionManager.authenticate_with_library_id(library_id, username=username)
        if user_auth is None:
            user_auth = UserSessionManager.create_library_id_user(library_id, username=username, password=password)

        messages.success(request, f'Account successfully created. Your username is: {user_auth.username}')

        request.session['user_auth_id'] = user_auth.id
        request.session['user_auth_method'] = user_auth.auth_method

        return redirect('user_dashboard')

    return render(request, 'user/register.html', {})


def user_logout(request):
    """Logout user"""
    if 'user_auth_id' in request.session:
        del request.session['user_auth_id']
        del request.session['user_auth_method']
    
    messages.success(request, 'You have been logged out.')
    return redirect('user_home')


def user_home(request):
    """Public home page for user side"""
    # Get or create anonymous user
    anon_user = UserSessionManager.get_or_create_anonymous_user(request)
    request.session['anon_user_id'] = anon_user.id
    
    # Get featured books
    featured_books = UserBook.objects.filter(
        is_banned=False,
        is_verified=True
    ).order_by('-rating_avg', '-view_count')[:6]
    
    # Get latest books
    latest_books = UserBook.objects.filter(
        is_banned=False,
        is_verified=True
    ).order_by('-created_at')[:6]
    
    context = {
        'featured_books': featured_books,
        'latest_books': latest_books,
        'is_authenticated': 'user_auth_id' in request.session,
    }
    return render(request, 'user/home.html', context)


# ========== DASHBOARD & PROFILE ==========

def user_dashboard(request):
    """User dashboard"""
    if 'user_auth_id' not in request.session:
        return redirect('user_login')
    
    user_auth_id = request.session.get('user_auth_id')
    try:
        user_auth = UserAuthentication.objects.get(id=user_auth_id)
    except UserAuthentication.DoesNotExist:
        return redirect('user_login')
    
    # Get user's uploaded books
    uploaded_books = UserBook.objects.filter(uploaded_by_user_id=request.session.get('anon_user_id'))
    
    # Get user's borrowed books (from library)
    borrowed_books = []
    if user_auth.member:
        borrowed_books = Transaction.objects.filter(
            member=user_auth.member,
            status='active'
        ).select_related('resource')
    
    # Get user's reviews
    user_reviews = UserReview.objects.filter(
        user_id=request.session.get('anon_user_id')
    ).select_related('book')
    
    context = {
        'user_auth': user_auth,
        'uploaded_books': uploaded_books,
        'borrowed_books': borrowed_books,
        'user_reviews': user_reviews,
    }
    return render(request, 'user/dashboard.html', context)


# ========== BOOK BROWSING & READING ==========

def user_browse_books(request):
    """Browse digital books with search and filter"""
    books = UserBook.objects.filter(
        is_banned=False,
        is_verified=True
    ).order_by('-created_at')
    
    resources = Resource.objects.filter(
        status='available'
    ).order_by('-created_at')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(resource_id__icontains=search_query)
        )
    
    # Filter by format
    book_format = request.GET.get('format', '')
    if book_format in ['pdf', 'epub']:
        books = books.filter(format=book_format)
    
    # Sort
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['-created_at', '-rating_avg', '-view_count', 'title']:
        books = books.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'resources': resources,
        'search_query': search_query,
        'book_format': book_format,
        'sort_by': sort_by,
        'is_authenticated': 'user_auth_id' in request.session,
    }
    return render(request, 'user/browse_books.html', context)


def user_book_detail(request, book_id):
    """View book details and reviews"""
    book = get_object_or_404(UserBook, id=book_id, is_banned=False)
    
    # Increment view count
    book.increment_view_count()
    
    # Get reviews
    reviews = book.reviews.filter(is_flagged=False).order_by('-created_at')
    
    # Get or create anonymous user for review form
    anon_user = None
    if 'anon_user_id' in request.session:
        try:
            anon_user = AnonymousUser.objects.get(id=request.session['anon_user_id'])
        except AnonymousUser.DoesNotExist:
            pass
    
    context = {
        'book': book,
        'reviews': reviews,
        'anon_user': anon_user,
    }
    return render(request, 'user/book_detail.html', context)


def user_resource_detail(request, resource_id):
    """Public detail for offline library resource (no admin redirect)"""
    resource = get_object_or_404(Resource, id=resource_id)
    transactions = Transaction.objects.filter(resource=resource)

    stats = {
        'total_borrowed': transactions.count(),
        'active_borrows': transactions.filter(status='active').count(),
        'returned': transactions.filter(status='returned').count(),
        'overdue': transactions.filter(status='overdue').count(),
    }

    context = {
        'resource': resource,
        'stats': stats,
    }
    return render(request, 'user/resource_detail.html', context)


def user_read_book_pdf(request, book_id):
    """Read PDF in browser"""
    book = get_object_or_404(UserBook, id=book_id, format='pdf', is_banned=False)
    
    # Generate absolute URL to avoid browser path issues
    book_url = request.build_absolute_uri(book.file.url)
    
    context = {
        'book': book,
        'book_url': book_url,
    }
    return render(request, 'user/read_pdf.html', context)


def user_read_book_epub(request, book_id):
    """Read EPUB in browser"""
    book = get_object_or_404(UserBook, id=book_id, format='epub', is_banned=False)
    
    book_url = request.build_absolute_uri(book.file.url)

    context = {
        'book': book,
        'book_url': book_url,
    }
    return render(request, 'user/read_epub.html', context)


def user_download_book(request, book_id):
    """Download book file"""
    book = get_object_or_404(UserBook, id=book_id, is_banned=False)
    
    # Increment download count
    book.increment_download_count()
    
    if book.file:
        response = FileResponse(book.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{book.title}.{book.format}"'
        return response
    
    return HttpResponse('File not found', status=404)


# ========== BOOK UPLOAD & MANAGEMENT ==========

@require_http_methods(["GET", "POST"])
def user_upload_book(request):
    """Upload a digital book (no login required)"""
    anon_user = UserSessionManager.get_or_create_anonymous_user(request)
    request.session['anon_user_id'] = anon_user.id

    if request.method == 'POST':
        form = UserBookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploaded_by_user = anon_user
            book.file_size = request.FILES['file'].size
            book.is_verified = False  # Admin must verify
            book.save()

            messages.success(request, 'Book uploaded successfully! Awaiting admin verification.')
            return redirect('user_dashboard')
    else:
        form = UserBookUploadForm()

    context = {'form': form}
    return render(request, 'user/upload_book.html', context)


def user_manage_uploads(request):
    """Manage user's uploaded books"""
    anon_user = None
    if 'anon_user_id' in request.session:
        try:
            anon_user = AnonymousUser.objects.get(id=request.session['anon_user_id'])
        except AnonymousUser.DoesNotExist:
            anon_user = None

    if not anon_user:
        anon_user = UserSessionManager.get_or_create_anonymous_user(request)
        request.session['anon_user_id'] = anon_user.id

    books = UserBook.objects.filter(uploaded_by_user=anon_user).order_by('-created_at')
    context = {'books': books}
    return render(request, 'user/manage_uploads.html', context)


# ========== REVIEWS & RATINGS ==========

@require_http_methods(["POST"])
def user_leave_review(request, book_id):
    """Leave a review on a book"""
    anon_user = None
    if 'anon_user_id' in request.session:
        try:
            anon_user = AnonymousUser.objects.get(id=request.session['anon_user_id'])
        except AnonymousUser.DoesNotExist:
            anon_user = None

    if not anon_user:
        anon_user = UserSessionManager.get_or_create_anonymous_user(request)
        request.session['anon_user_id'] = anon_user.id

    book = get_object_or_404(UserBook, id=book_id, is_banned=False)
    
    # Check if user already reviewed this book
    existing_review = UserReview.objects.filter(book=book, user=anon_user).exists()
    if existing_review:
        return JsonResponse({'error': 'You have already reviewed this book'}, status=400)
    
    form = UserReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.book = book
        review.user = anon_user
        review.save()
        
        # Update book's average rating
        avg_rating = book.reviews.aggregate(Avg('rating'))['rating__avg']
        book.rating_avg = avg_rating or 0
        book.review_count = book.reviews.count()
        book.save(update_fields=['rating_avg', 'review_count'])
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Review posted!'})
        else:
            messages.success(request, 'Your review has been posted!')
            return redirect('user_book_detail', book_id=book.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid form data'}, status=400)
    else:
        messages.error(request, 'Error posting review.')
        return redirect('user_book_detail', book_id=book.id)


# ========== LIBRARY BORROWING (PHYSICAL BOOKS) ==========

def user_borrow_library_book(request):
    """Browse library books and borrow"""
    # Must be authenticated to borrow
    if 'user_auth_id' not in request.session:
        messages.info(request, 'Please login to borrow books.')
        return redirect('user_login')
    
    user_auth_id = request.session.get('user_auth_id')
    try:
        user_auth = UserAuthentication.objects.get(id=user_auth_id)
    except UserAuthentication.DoesNotExist:
        return redirect('user_login')
    
    # Must have associated member
    if not user_auth.member:
        messages.error(request, 'Your account is not linked to a member record.')
        return redirect('user_dashboard')
    
    # Get available books
    books = Resource.objects.filter(
        available_quantity__gt=0,
        status='available'
    ).order_by('title')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(resource_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'user/borrow_library_books.html', context)


@require_http_methods(["POST"])
def user_checkout_book(request, resource_id):
    """Checkout a library book"""
    if 'user_auth_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=403)
    
    user_auth_id = request.session.get('user_auth_id')
    try:
        user_auth = UserAuthentication.objects.get(id=user_auth_id)
        resource = Resource.objects.get(id=resource_id, available_quantity__gt=0)
    except (UserAuthentication.DoesNotExist, Resource.DoesNotExist):
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    if not user_auth.member:
        return JsonResponse({'error': 'Member record not found'}, status=400)
    
    # Create transaction
    due_date = timezone.now().date() + timedelta(days=15)
    transaction = Transaction.objects.create(
        resource=resource,
        member=user_auth.member,
        due_date=due_date,
        status='active'
    )
    
    # Update resource availability
    resource.available_quantity -= 1
    resource.save(update_fields=['available_quantity'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Book checked out! Due date: {due_date}',
            'due_date': str(due_date)
        })
    else:
        messages.success(request, f'Book checked out successfully! Due date: {due_date}')
        return redirect('user_borrow_library_book')


def user_return_book(request):
    """Return a borrowed library book"""
    if 'user_auth_id' not in request.session:
        return redirect('user_login')
    
    user_auth_id = request.session.get('user_auth_id')
    try:
        user_auth = UserAuthentication.objects.get(id=user_auth_id)
    except UserAuthentication.DoesNotExist:
        return redirect('user_login')
    
    if not user_auth.member:
        messages.error(request, 'Member record not found.')
        return redirect('user_dashboard')
    
    # Get borrowed books
    borrowed_books = Transaction.objects.filter(
        member=user_auth.member,
        status='active'
    ).select_related('resource')
    
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        try:
            transaction = Transaction.objects.get(
                id=transaction_id,
                member=user_auth.member,
                status='active'
            )
            transaction.mark_returned()
            messages.success(request, f'Book "{transaction.resource.title}" returned successfully!')
            return redirect('user_dashboard')
        except Transaction.DoesNotExist:
            messages.error(request, 'Transaction not found.')
    
    context = {'borrowed_books': borrowed_books}
    return render(request, 'user/return_book.html', context)

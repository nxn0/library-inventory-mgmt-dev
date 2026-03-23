from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Resource, Category, Member, Transaction, StockLog
from .forms import ResourceForm, CategoryForm, MemberForm, CheckoutForm, StockLogForm, SearchForm


# ============= DASHBOARD =============
def dashboard(request):
    """Main dashboard with statistics"""
    total_resources = Resource.objects.count()
    total_members = Member.objects.filter(is_active=True).count()
    checked_out = Transaction.objects.filter(status='active').count()
    overdue = Transaction.objects.filter(
        status='active',
        due_date__lt=timezone.now().date()
    ).count()
    
    # Low stock items (less than 3 available)
    low_stock = Resource.objects.filter(available_quantity__lt=3, available_quantity__gt=0)
    
    # Recent transactions
    recent_transactions = Transaction.objects.select_related('resource', 'member')[:10]
    
    # Popular categories
    popular_categories = Category.objects.annotate(
        resource_count=Count('resources')
    ).order_by('-resource_count')[:5]
    
    context = {
        'total_resources': total_resources,
        'total_members': total_members,
        'checked_out': checked_out,
        'overdue': overdue,
        'low_stock': low_stock,
        'recent_transactions': recent_transactions,
        'popular_categories': popular_categories,
    }
    return render(request, 'dashboard.html', context)


# ============= RESOURCE CRUD =============
def resource_list(request):
    """List all resources with search and filter"""
    resources = Resource.objects.select_related('category').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(resource_id__icontains=search_query) |
            Q(author__icontains=search_query)
        )
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        resources = resources.filter(category_id=category_id)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        resources = resources.filter(status=status)
    
    categories = Category.objects.all()
    
    context = {
        'resources': resources,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'resource_list.html', context)


def resource_detail(request, pk):
    """View single resource details"""
    resource = get_object_or_404(Resource, pk=pk)
    transactions = resource.transactions.select_related('member').all()[:10]
    stock_logs = resource.stock_logs.all()[:10]
    
    context = {
        'resource': resource,
        'transactions': transactions,
        'stock_logs': stock_logs,
    }
    return render(request, 'resource_detail.html', context)


def resource_create(request):
    """Create new resource"""
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save()
            
            # Create initial stock log
            StockLog.objects.create(
                resource=resource,
                action='add',
                quantity=resource.total_quantity,
                reason='Initial stock entry'
            )
            
            messages.success(request, f'Resource "{resource.title}" created successfully!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'resource_form.html', context)


def resource_edit(request, pk):
    """Edit existing resource"""
    resource = get_object_or_404(Resource, pk=pk)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f'Resource "{resource.title}" updated successfully!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)
    
    context = {'form': form, 'action': 'Edit', 'resource': resource}
    return render(request, 'resource_form.html', context)


def resource_delete(request, pk):
    """Delete resource"""
    resource = get_object_or_404(Resource, pk=pk)
    
    if request.method == 'POST':
        title = resource.title
        resource.delete()
        messages.success(request, f'Resource "{title}" deleted successfully!')
        return redirect('resource_list')
    
    context = {'object': resource, 'object_name': 'Resource'}
    return render(request, 'confirm_delete.html', context)


# ============= MEMBER CRUD =============
def member_list(request):
    """List all members"""
    members = Member.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(member_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by type
    member_type = request.GET.get('type', '')
    if member_type:
        members = members.filter(member_type=member_type)
    
    context = {
        'members': members,
        'search_query': search_query,
    }
    return render(request, 'member_list.html', context)


def member_detail(request, pk):
    """View member details"""
    member = get_object_or_404(Member, pk=pk)
    transactions = member.transactions.select_related('resource').all()[:10]
    
    context = {
        'member': member,
        'transactions': transactions,
    }
    return render(request, 'member_detail.html', context)


def member_create(request):
    """Generate QR code for member registration"""
    import qrcode
    import io
    import base64
    
    # Generate a unique registration token
    import uuid
    token = str(uuid.uuid4())
    
    # Store token in session for verification
    request.session['registration_token'] = token
    
    # Create QR code with URL to registration page
    registration_url = request.build_absolute_uri(f'/members/register/{token}/')
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(registration_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    
    # Convert to base64 for display in template
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'qr_code': img_str,
        'registration_url': registration_url,
        'token': token
    }
    return render(request, 'member_register.html', context)


def member_register(request, token):
    """Handle fingerprint-based member registration"""
    # Verify token
    if request.session.get('registration_token') != token:
        messages.error(request, 'Invalid registration token.')
        return redirect('member_list')
    
    if request.method == 'POST':
        fingerprint_data = request.POST.get('fingerprint_data')
        if fingerprint_data:
            import hashlib
            import json
            
            # Hash the fingerprint data
            hashed_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            # Check if member already exists
            if Member.objects.filter(hashed_fingerprint=hashed_fingerprint).exists():
                messages.warning(request, 'Member with this fingerprint already exists.')
                return redirect('member_list')
            
            # Create new member
            member = Member.objects.create(hashed_fingerprint=hashed_fingerprint)
            messages.success(request, f'Member {member.member_id} registered successfully!')
            
            # Clear session token
            del request.session['registration_token']
            
            return redirect('member_detail', pk=member.pk)
        else:
            messages.error(request, 'Fingerprint data is required.')
    
    context = {'token': token}
    return render(request, 'member_fingerprint.html', context)


def member_edit(request, pk):
    """Edit member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member {member.member_id} updated successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = MemberForm(instance=member)
    
    context = {'form': form, 'action': 'Edit', 'member': member}
    return render(request, 'member_form.html', context)


def member_delete(request, pk):
    """Delete member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        name = f"Member {member.member_id}"
        member.delete()
        messages.success(request, f'Member "{name}" deleted successfully!')
        return redirect('member_list')
    
    context = {'object': member, 'object_name': 'Member'}
    return render(request, 'confirm_delete.html', context)


# ============= CATEGORY CRUD =============
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(resource_count=Count('resources'))
    
    context = {'categories': categories}
    return render(request, 'category_list.html', context)


def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'category_form.html', context)


def category_edit(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'action': 'Edit', 'category': category}
    return render(request, 'category_form.html', context)


def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('category_list')
    
    context = {'object': category, 'object_name': 'Category'}
    return render(request, 'confirm_delete.html', context)


# ============= TRANSACTIONS =============
def checkout_create(request):
    """Checkout resource to member"""
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            resource = form.cleaned_data['resource']
            member = form.cleaned_data['member']
            due_days = form.cleaned_data['due_days']
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction
            due_date = timezone.now().date() + timedelta(days=due_days)
            transaction = Transaction.objects.create(
                resource=resource,
                member=member,
                due_date=due_date,
                notes=notes
            )
            
            # Update resource availability
            resource.available_quantity -= 1
            if resource.available_quantity == 0:
                resource.status = 'unavailable'
            resource.save()
            
            messages.success(request, f'Successfully checked out "{resource.title}" to Member {member.member_id}')
            return redirect('transaction_list')
    else:
        form = CheckoutForm()
    
    context = {'form': form, 'action': 'Checkout'}
    return render(request, 'checkout_form.html', context)


def return_resource(request):
    """Return checked out resource"""
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        transaction = get_object_or_404(Transaction, pk=transaction_id, status='active')
        
        transaction.mark_returned()
        
        messages.success(request, f'Resource returned: {transaction.resource.title}')
        return redirect('transaction_list')
    
    # List active transactions for return
    active_transactions = Transaction.objects.filter(status='active').select_related('resource', 'member')
    context = {'transactions': active_transactions}
    return render(request, 'return_form.html', context)


def transaction_list(request):
    """List all transactions"""
    transactions = Transaction.objects.select_related('resource', 'member').all()
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        transactions = transactions.filter(status=status)
    
    context = {'transactions': transactions}
    return render(request, 'transaction_list.html', context)

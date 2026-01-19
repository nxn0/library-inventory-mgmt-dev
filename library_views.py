from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Resource, Category, Member, Transaction, StockLog
from .forms import ResourceForm, CategoryForm, MemberForm, CheckoutForm, StockLogForm

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
    return render(request, 'library/dashboard.html', context)


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
    return render(request, 'library/resource_list.html', context)


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
    return render(request, 'library/resource_detail.html', context)


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
                reason='Initial stock',
                performed_by=request.user.username if request.user.is_authenticated else 'Admin'
            )
            
            messages.success(request, f'Resource "{resource.title}" created successfully!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm()
    
    return render(request, 'library/resource_form.html', {'form': form, 'action': 'Create'})


def resource_update(request, pk):
    """Update existing resource"""
    resource = get_object_or_404(Resource, pk=pk)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f'Resource "{resource.title}" updated successfully!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)
    
    return render(request, 'library/resource_form.html', {'form': form, 'action': 'Update', 'resource': resource})


def resource_delete(request, pk):
    """Delete resource"""
    resource = get_object_or_404(Resource, pk=pk)
    
    if request.method == 'POST':
        title = resource.title
        resource.delete()
        messages.success(request, f'Resource "{title}" deleted successfully!')
        return redirect('resource_list')
    
    return render(request, 'library/resource_confirm_delete.html', {'resource': resource})


# ============= CATEGORY CRUD =============
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(resource_count=Count('resources'))
    return render(request, 'library/category_list.html', {'categories': categories})


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
    
    return render(request, 'library/category_form.html', {'form': form, 'action': 'Create'})


def category_update(request, pk):
    """Update category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'library/category_form.html', {'form': form, 'action': 'Update'})


def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('category_list')
    
    return render(request, 'library/category_confirm_delete.html', {'category': category})


# ============= MEMBER CRUD =============
def member_list(request):
    """List all members"""
    members = Member.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(member_id__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    return render(request, 'library/member_list.html', {'members': members, 'search_query': search_query})


def member_detail(request, pk):
    """View single member details"""
    member = get_object_or_404(Member, pk=pk)
    transactions = member.transactions.select_related('resource').all()[:10]
    active_checkouts = member.transactions.filter(status='active').select_related('resource')
    
    context = {
        'member': member,
        'transactions': transactions,
        'active_checkouts': active_checkouts,
    }
    return render(request, 'library/member_detail.html', context)


def member_create(request):
    """Create new member"""
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Member "{member.full_name}" created successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = MemberForm()
    
    return render(request, 'library/member_form.html', {'form': form, 'action': 'Create'})


def member_update(request, pk):
    """Update member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member "{member.full_name}" updated successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = MemberForm(instance=member)
    
    return render(request, 'library/member_form.html', {'form': form, 'action': 'Update'})


def member_delete(request, pk):
    """Delete member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f'Member "{name}" deleted successfully!')
        return redirect('member_list')
    
    return render(request, 'library/member_confirm_delete.html', {'member': member})


# ============= TRANSACTION MANAGEMENT =============
def checkout_resource(request):
    """Check out a resource to a member"""
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            resource = form.cleaned_data['resource']
            member = form.cleaned_data['member']
            due_days = form.cleaned_data['due_days']
            
            # Check if resource is available
            if resource.available_quantity <= 0:
                messages.error(request, 'This resource is not available for checkout!')
                return redirect('checkout_resource')
            
            # Create transaction
            transaction = Transaction.objects.create(
                resource=resource,
                member=member,
                transaction_type='checkout',
                due_date=timezone.now().date() + timedelta(days=due_days),
                status='active'
            )
            
            # Update resource availability
            resource.available_quantity -= 1
            if resource.available_quantity == 0:
                resource.status = 'checked_out'
            resource.save()
            
            messages.success(request, f'"{resource.title}" checked out to {member.full_name} successfully!')
            return redirect('transaction_list')
    else:
        form = CheckoutForm()
    
    return render(request, 'library/checkout_form.html', {'form': form})


def checkin_resource(request, transaction_id):
    """Check in a resource"""
    transaction = get_object_or_404(Transaction, pk=transaction_id, status='active')
    
    if request.method == 'POST':
        transaction.return_date = timezone.now()
        transaction.status = 'returned'
        
        # Calculate fine if overdue
        if transaction.is_overdue:
            transaction.fine_amount = transaction.calculate_fine()
        
        transaction.save()
        
        # Update resource availability
        resource = transaction.resource
        resource.available_quantity += 1
        if resource.status == 'checked_out':
            resource.status = 'available'
        resource.save()
        
        messages.success(request, f'"{resource.title}" checked in successfully!')
        if transaction.fine_amount > 0:
            messages.warning(request, f'Fine amount: ${transaction.fine_amount}')
        
        return redirect('transaction_list')
    
    return render(request, 'library/checkin_confirm.html', {'transaction': transaction})


def transaction_list(request):
    """List all transactions"""
    transactions = Transaction.objects.select_related('resource', 'member').all()
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        transactions = transactions.filter(status=status)
    
    return render(request, 'library/transaction_list.html', {'transactions': transactions})


# ============= STOCK MANAGEMENT =============
def stock_log_create(request, resource_id):
    """Add stock log entry"""
    resource = get_object_or_404(Resource, pk=resource_id)
    
    if request.method == 'POST':
        form = StockLogForm(request.POST)
        if form.is_valid():
            stock_log = form.save(commit=False)
            stock_log.resource = resource
            stock_log.performed_by = request.user.username if request.user.is_authenticated else 'Admin'
            stock_log.save()
            
            # Update resource quantities
            if stock_log.action == 'add':
                resource.total_quantity += stock_log.quantity
                resource.available_quantity += stock_log.quantity
            elif stock_log.action in ['remove', 'damage', 'lost']:
                resource.total_quantity -= stock_log.quantity
                resource.available_quantity = max(0, resource.available_quantity - stock_log.quantity)
            
            resource.save()
            
            messages.success(request, f'Stock log entry created for "{resource.title}"!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = StockLogForm()
    
    return render(request, 'library/stock_log_form.html', {'form': form, 'resource': resource})
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Category(models.Model):
    """Resource categories like Books, Magazines, Equipment, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Resource(models.Model):
    """Main resource model - books, equipment, magazines, etc."""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('checked_out', 'Checked Out'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    title = models.CharField(max_length=255)
    resource_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier (ISBN, Serial No, etc)")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='resources')
    author = models.CharField(max_length=255, blank=True, help_text="Author/Manufacturer")
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    total_quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    available_quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    shelf_location = models.CharField(max_length=100, blank=True, help_text="Physical location in library")
    acquisition_date = models.DateField(default=timezone.now)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='resources/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.resource_id})"
    
    @property
    def is_available(self):
        return self.available_quantity > 0 and self.status == 'available'


class Member(models.Model):
    """Library members who can check out resources"""
    MEMBER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    ]
    
    member_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES)
    department = models.CharField(max_length=100, blank=True)
    join_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Transaction(models.Model):
    """Check-in/Check-out transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('checkout', 'Check Out'),
        ('checkin', 'Check In'),
        ('renew', 'Renew'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name='transactions')
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    checkout_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-checkout_date']
    
    def __str__(self):
        return f"{self.resource.title} - {self.member.full_name} ({self.checkout_date.date()})"
    
    @property
    def is_overdue(self):
        if self.status == 'active' and self.due_date < timezone.now().date():
            return True
        return False
    
    def calculate_fine(self, rate_per_day=5.00):
        """Calculate fine for overdue items"""
        if self.is_overdue:
            days_overdue = (timezone.now().date() - self.due_date).days
            return days_overdue * rate_per_day
        return 0.00


class StockLog(models.Model):
    """Track additions/removals of resources"""
    ACTION_CHOICES = [
        ('add', 'Added to Stock'),
        ('remove', 'Removed from Stock'),
        ('damage', 'Marked as Damaged'),
        ('lost', 'Marked as Lost'),
        ('repair', 'Sent for Repair'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='stock_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reason = models.TextField(blank=True)
    performed_by = models.CharField(max_length=100, help_text="Name of staff member")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.resource.title} (Qty: {self.quantity})"
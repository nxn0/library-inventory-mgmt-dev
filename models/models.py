from django.db import models
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    """Resource categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Resource(models.Model):
    """Library resources (books, magazines, equipment, etc.)"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]

    title = models.CharField(max_length=255)
    resource_id = models.CharField(max_length=50, unique=True, help_text="ISBN or serial number")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='resources')
    author = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Inventory tracking
    total_quantity = models.IntegerField(default=1)
    available_quantity = models.IntegerField(default=1)
    shelf_location = models.CharField(max_length=50, blank=True)
    
    # Additional info
    acquisition_date = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
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
    """Library members identified by browser fingerprint"""
    
    member_id = models.CharField(max_length=50, unique=True)
    hashed_fingerprint = models.CharField(max_length=128, unique=True, null=True, blank=True, help_text="SHA-256 hash of browser fingerprint data")
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Member {self.member_id}"

    def save(self, *args, **kwargs):
        if not self.member_id:
            # Generate a unique member ID
            import uuid
            self.member_id = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Checkout/checkin transactions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='transactions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='transactions')
    checkout_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-checkout_date']

    def __str__(self):
        return f"{self.resource.title} - Member {self.member.member_id}"

    @property
    def is_overdue(self):
        return self.status == 'active' and timezone.now().date() > self.due_date

    def mark_returned(self):
        self.status = 'returned'
        self.return_date = timezone.now()
        self.save()
        
        # Update resource availability
        self.resource.available_quantity += 1
        self.resource.save()


class StockLog(models.Model):
    """Track inventory changes"""
    ACTION_CHOICES = [
        ('add', 'Added'),
        ('remove', 'Removed'),
        ('repair', 'Repaired'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='stock_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField()
    reason = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.resource.title} - {self.action} ({self.quantity})"

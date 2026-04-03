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
    """Library members - supports both traditional and fingerprint-based registration"""
    
    # Basic identification
    member_id = models.CharField(max_length=50, unique=True)
    
    # Traditional member fields (optional for fingerprint-based)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    member_type = models.CharField(max_length=20, choices=[
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('external', 'External'),
    ], default='student', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    # Fingerprint-based identification
    hashed_fingerprint = models.CharField(max_length=128, unique=True, null=True, blank=True, help_text="SHA-256 hash of browser fingerprint data")
    
    # Common fields
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.member_id})"
        else:
            return f"Member {self.member_id}"

    def save(self, *args, **kwargs):
        if not self.member_id:
            # Generate a unique member ID
            import uuid
            self.member_id = str(uuid.uuid4())[:8].upper()
        
        # Hash personal data if provided (for manual registration)
        if self.first_name or self.last_name or self.email or self.phone:
            import hashlib
            import json
            personal_data = {
                'first_name': self.first_name or '',
                'last_name': self.last_name or '',
                'email': self.email or '',
                'phone': self.phone or ''
            }
            data_str = json.dumps(personal_data, sort_keys=True)
            self.hashed_personal_data = hashlib.sha256(data_str.encode()).hexdigest()
        
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return f"Member {self.member_id}"


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


# ========== USER-SIDE MODELS ==========

class AnonymousUser(models.Model):
    """Track anonymous users with session-based identification"""
    user_id = models.CharField(max_length=255, unique=True)  # UUID
    fingerprint_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 hash of browser fingerprint")
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['is_active', 'last_activity']),
        ]
    
    def __str__(self):
        return f"Anonymous User: {self.user_id}"
    
    @property
    def is_expired(self):
        """Check if user has been inactive for 30 days"""
        from datetime import timedelta
        expiry_date = self.last_activity + timedelta(days=30)
        return timezone.now() > expiry_date


class UserAuthentication(models.Model):
    """Store encrypted user authentication credentials"""
    AUTH_METHODS = [
        ('library_id', 'Library ID'),
        ('student_id', 'Student ID'),
        ('credentials', 'Name + Phone + Credentials'),
    ]
    
    # Encrypted identifier - use one of these
    encrypted_library_id = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    encrypted_auth_data = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    
    auth_method = models.CharField(max_length=20, choices=AUTH_METHODS)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Optional association with library member
    member = models.OneToOneField(Member, on_delete=models.CASCADE, null=True, blank=True, related_name='user_auth')
    
    # User info (minimal, optional)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    ban_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_banned']),
        ]
    
    def __str__(self):
        return f"User Auth - Method: {self.auth_method}"


class UserBook(models.Model):
    """Digital books uploaded by users"""
    BOOK_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
    ]
    
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    resource_id = models.CharField(max_length=50, blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_books')
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    format = models.CharField(max_length=10, choices=BOOK_FORMAT_CHOICES)
    shelf_location = models.CharField(max_length=50, blank=True, default='')
    
    # File storage
    file = models.FileField(upload_to='user_books/%Y/%m/%d/')
    file_size = models.BigIntegerField()  # In bytes

    # Metadata
    cover_image = models.ImageField(upload_to='user_books/covers/', null=True, blank=True)
    pages_count = models.IntegerField(null=True, blank=True)
    
    # User info (anonymous)
    uploaded_by_user = models.ForeignKey(AnonymousUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_books')
    
    # Status
    is_verified = models.BooleanField(default=False, help_text="Admin verification status")
    is_banned = models.BooleanField(default=False, help_text="Banned by admin")
    ban_reason = models.TextField(blank=True)
    
    # Stats
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_banned']),
            models.Index(fields=['rating_avg']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author or 'Unknown'}"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])


class UserReview(models.Model):
    """Reviews left by anonymous users on digital books"""
    book = models.ForeignKey(UserBook, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(AnonymousUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)])
    
    is_flagged = models.BooleanField(default=False, help_text="Admin flagged for inappropriate content")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['book', 'user']  # One review per user per book
    
    def __str__(self):
        return f"Review of {self.book.title} - {self.rating} stars"


class UserBan(models.Model):
    """Track banned users for moderation purposes"""
    BAN_REASONS = [
        ('inappropriate_content', 'Inappropriate Content Upload'),
        ('multiple_violations', 'Multiple Policy Violations'),
        ('overdue_books', 'Overdue Books Not Returned'),
        ('harassment', 'Harassment/Abuse'),
        ('other', 'Other'),
    ]
    
    user_auth = models.OneToOneField(UserAuthentication, on_delete=models.CASCADE, related_name='ban')
    reason = models.CharField(max_length=50, choices=BAN_REASONS)
    description = models.TextField()
    banned_by = models.CharField(max_length=255, blank=True)  # Admin username or ID
    
    is_permanent = models.BooleanField(default=False)
    ban_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ban - {self.user_auth.auth_method}: {self.reason}"
    
    @property
    def is_active(self):
        if self.is_permanent:
            return True
        return timezone.now() < self.ban_until if self.ban_until else False


class Fine(models.Model):
    """Track fines for overdue books"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='fines')
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='fine')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    days_overdue = models.IntegerField()
    reason = models.TextField(blank=True)
    
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_paid']),
            models.Index(fields=['member']),
        ]
    
    def __str__(self):
        return f"Fine - {self.member.member_id}: Rs. {self.amount}"


class OverdueBook(models.Model):
    """Track overdue books - moved here after 30+ days, unencrypted for admin viewing"""
    # Unencrypted user info (only for overdue items)
    user_identifier = models.CharField(max_length=255)  # Could be name, phone, ID
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Book info
    book_title = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255, blank=True)
    resource_id = models.CharField(max_length=50)
    
    # Dates
    checkout_date = models.DateField()
    due_date = models.DateField()
    days_overdue = models.IntegerField(default=0)
    
    # Related transaction
    original_transaction = models.CharField(max_length=255, null=True, blank=True)
    
    # Status
    is_recovered = models.BooleanField(default=False)
    recovery_date = models.DateTimeField(null=True, blank=True)
    fine_imposed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-days_overdue']
        indexes = [
            models.Index(fields=['is_recovered']),
            models.Index(fields=['-days_overdue']),
        ]
    
    def __str__(self):
        return f"Overdue: {self.book_title} - {self.user_identifier}"

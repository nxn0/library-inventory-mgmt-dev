from django.contrib import admin
from .models import (
    Category, Resource, Member, Transaction, StockLog,
    UserBook, UserReview, AnonymousUser, UserAuthentication,
    UserBan, Fine, OverdueBook
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_id', 'category', 'author', 'total_quantity', 'available_quantity', 'status', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['title', 'resource_id', 'author']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'resource_id', 'category', 'author', 'publisher', 'publication_year')
        }),
        ('Description', {
            'fields': ('description', 'image')
        }),
        ('Inventory', {
            'fields': ('total_quantity', 'available_quantity', 'shelf_location', 'status')
        }),
        ('Financial & Acquisition', {
            'fields': ('cost', 'acquisition_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['member_id', 'full_name', 'email', 'member_type', 'hashed_fingerprint', 'is_active', 'join_date', 'created_at']
    list_filter = ['member_type', 'is_active', 'join_date']
    search_fields = ['member_id', 'first_name', 'last_name', 'email', 'hashed_fingerprint']
    list_editable = ['is_active']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('member_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Membership Details', {
            'fields': ('member_type', 'department', 'join_date', 'is_active')
        }),
        ('Fingerprint Data', {
            'fields': ('hashed_fingerprint',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['hashed_fingerprint', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['resource', 'member', 'checkout_date', 'due_date', 'status']
    list_filter = ['status', 'checkout_date', 'due_date']
    search_fields = ['resource__title', 'member__first_name', 'member__last_name']
    ordering = ['-checkout_date']
    readonly_fields = ['checkout_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('resource', 'member', 'checkout_date', 'due_date', 'return_date', 'status')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ['resource', 'action', 'quantity', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['resource__title', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('resource', 'action', 'quantity', 'created_by')
        }),
        ('Details', {
            'fields': ('reason',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ========== USER-SIDE ADMIN ==========

@admin.register(AnonymousUser)
class AnonymousUserAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'fingerprint_hash', 'ip_address', 'created_at', 'last_activity', 'is_active']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user_id', 'fingerprint_hash', 'ip_address']
    readonly_fields = ['user_id', 'fingerprint_hash', 'created_at', 'last_activity']
    ordering = ['-last_activity']


@admin.register(UserAuthentication)
class UserAuthenticationAdmin(admin.ModelAdmin):
    list_display = ['id', 'auth_method', 'member', 'is_active', 'is_banned', 'created_at']
    list_filter = ['auth_method', 'is_active', 'is_banned', 'created_at']
    search_fields = ['encrypted_library_id', 'member__member_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'format', 'is_verified', 'is_banned', 'rating_avg', 'created_at']
    list_filter = ['format', 'is_verified', 'is_banned', 'created_at']
    search_fields = ['title', 'author']
    list_editable = ['is_verified', 'is_banned']
    readonly_fields = ['view_count', 'download_count', 'rating_avg', 'review_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'author', 'description', 'format')
        }),
        ('File Details', {
            'fields': ('file', 'file_size', 'pages_count', 'cover_image')
        }),
        ('Status & Moderation', {
            'fields': ('is_verified', 'is_banned', 'ban_reason', 'uploaded_by_user')
        }),
        ('Statistics', {
            'fields': ('view_count', 'download_count', 'rating_avg', 'review_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserReview)
class UserReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'rating', 'is_flagged', 'created_at']
    list_filter = ['rating', 'is_flagged', 'created_at']
    search_fields = ['book__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = ['user_auth', 'reason', 'is_permanent', 'ban_until', 'created_at']
    list_filter = ['reason', 'is_permanent', 'created_at']
    search_fields = ['user_auth__id', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'days_overdue', 'is_paid', 'created_at']
    list_filter = ['is_paid', 'created_at']
    search_fields = ['member__member_id', 'member__first_name', 'member__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(OverdueBook)
class OverdueBookAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'user_identifier', 'days_overdue', 'is_recovered', 'created_at']
    list_filter = ['is_recovered', 'created_at', 'days_overdue']
    search_fields = ['book_title', 'user_identifier', 'name', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-days_overdue']

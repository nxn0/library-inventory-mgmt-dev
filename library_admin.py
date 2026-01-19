from django.contrib import admin
from .models import Category, Resource, Member, Transaction, StockLog

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
    list_display = ['member_id', 'full_name', 'email', 'member_type', 'is_active', 'join_date']
    list_filter = ['member_type', 'is_active', 'join_date']
    search_fields = ['member_id', 'first_name', 'last_name', 'email']
    list_editable = ['is_active']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('member_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Membership Details', {
            'fields': ('member_type', 'department', 'join_date', 'is_active')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'resource', 'member', 'transaction_type', 'checkout_date', 'due_date', 'return_date', 'status', 'fine_amount']
    list_filter = ['transaction_type', 'status', 'checkout_date']
    search_fields = ['resource__title', 'member__first_name', 'member__last_name', 'member__member_id']
    readonly_fields = ['created_at', 'checkout_date']
    ordering = ['-checkout_date']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('resource', 'member', 'transaction_type', 'status')
        }),
        ('Dates', {
            'fields': ('checkout_date', 'due_date', 'return_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'fine_amount')
        }),
    )


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'resource', 'action', 'quantity', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['resource__title', 'performed_by']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Stock Action', {
            'fields': ('resource', 'action', 'quantity')
        }),
        ('Details', {
            'fields': ('reason', 'performed_by', 'timestamp')
        }),
    )
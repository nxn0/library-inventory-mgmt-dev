from django import forms
from .models import (
    Resource, Category, Member, Transaction, StockLog,
    UserBook, UserReview, UserAuthentication, Fine, UserBan
)
from datetime import timedelta
from django.utils import timezone


# ========== ADMIN FORMS ==========

class ResourceForm(forms.ModelForm):
    """Form for creating/updating resources"""
    class Meta:
        model = Resource
        fields = [
            'title', 'resource_id', 'category', 'author', 'publisher',
            'publication_year', 'description', 'total_quantity', 
            'available_quantity', 'shelf_location', 'acquisition_date',
            'cost', 'status', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'resource_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN/Serial No'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author/Manufacturer'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Publisher'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'shelf_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., A-101'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        total_qty = cleaned_data.get('total_quantity')
        available_qty = cleaned_data.get('available_quantity')
        
        if total_qty and available_qty and available_qty > total_qty:
            raise forms.ValidationError('Available quantity cannot exceed total quantity!')
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Form for creating/updating categories"""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category description'}),
        }


class MemberForm(forms.ModelForm):
    """Form for creating/updating members (supports both traditional and fingerprint-based)"""
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 
            'phone', 'member_type', 'department', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'member_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CheckoutForm(forms.Form):
    """Form for checking out resources"""
    resource = forms.ModelChoiceField(
        queryset=Resource.objects.filter(available_quantity__gt=0, status='available'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Resource'
    )
    member = forms.ModelChoiceField(
        queryset=Member.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Member'
    )
    due_days = forms.IntegerField(
        initial=15,
        min_value=1,
        max_value=90,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Due in (days)',
        help_text='Number of days until the resource is due back'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes'}),
        label='Notes'
    )


class StockLogForm(forms.ModelForm):
    """Form for adding stock log entries"""
    class Meta:
        model = StockLog
        fields = ['action', 'quantity', 'reason']
        widgets = {
            'action': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for this action'}),
        }


class SearchForm(forms.Form):
    """Generic search form"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...',
        })
    )


class FineForm(forms.ModelForm):
    """Form for creating/imposing fines"""
    class Meta:
        model = Fine
        fields = ['member', 'resource', 'amount', 'days_overdue', 'reason']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'resource': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'days_overdue': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserBanForm(forms.ModelForm):
    """Form for banning/suspending users"""
    class Meta:
        model = UserBan
        fields = ['reason', 'description', 'is_permanent', 'ban_until']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_permanent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ban_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


# ========== USER-SIDE FORMS ==========

class UserLoginForm(forms.Form):
    """Form for user login with privacy-first approach"""
    LOGIN_METHOD_CHOICES = [
        ('library_id', 'Library ID / Student ID'),
        ('username', 'Username + Password'),
        ('credentials', 'Full Name + Phone + Password'),
    ]
    
    login_method = forms.ChoiceField(
        choices=LOGIN_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    
    # Library ID / Student ID login
    library_id = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Library/Student ID',
        })
    )

    # Username login
    username = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
        })
    )
    password = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )
    
    # For Name + Phone + Credentials
    user_name = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name',
        })
    )
    
    user_phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number',
        })
    )
    
    credentials = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        login_method = cleaned_data.get('login_method')

        if login_method in ['library_id', 'student_id']:
            if not cleaned_data.get('library_id'):
                raise forms.ValidationError('Please enter your Library/Student ID')
            # username is optional; it will be generated if missing

        elif login_method == 'username':
            if not cleaned_data.get('username') or not cleaned_data.get('password'):
                raise forms.ValidationError('Please enter your username and password')

        elif login_method == 'credentials':
            if not cleaned_data.get('user_name') or not cleaned_data.get('user_phone') or not cleaned_data.get('credentials'):
                raise forms.ValidationError('Please fill in all fields for registration')

        return cleaned_data


class UserBookUploadForm(forms.ModelForm):
    """Form for uploading digital books"""
    class Meta:
        model = UserBook
        fields = ['title', 'author', 'description', 'format', 'file', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Book Title',
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Author Name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Book Description',
            }),
            'format': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.epub',
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }


class UserReviewForm(forms.ModelForm):
    """Form for leaving reviews on digital books"""
    class Meta:
        model = UserReview
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Review Title (optional)',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your thoughts about this book...',
            }),
            'rating': forms.Select(attrs={'class': 'form-control'}),
        }
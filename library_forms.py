from django import forms
from .models import Resource, Category, Member, Transaction, StockLog

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
    """Form for creating/updating members"""
    class Meta:
        model = Member
        fields = [
            'member_id', 'first_name', 'last_name', 'email', 
            'phone', 'member_type', 'department', 'join_date', 'is_active'
        ]
        widgets = {
            'member_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique member ID'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'member_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
        initial=14,
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
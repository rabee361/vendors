from django import forms
from django.contrib.auth.models import User
from .models import Category

class BuyerLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'buyerEmail',
        'placeholder': 'name@example.com',
        'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'buyerPass',
        'placeholder': '••••••••',
        'required': True
    }))

class SellerLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'sEmail',
        'placeholder': 'seller@store.com',
        'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'sPass',
        'placeholder': '••••••••',
        'required': True
    }))

class SellerRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'fullName',
        'placeholder': 'مثال: أحمد خالد',
        'required': True
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'email',
        'placeholder': 'name@example.com',
        'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'password',
        'placeholder': '••••••••',
        'required': True
    }))
    address = forms.CharField(max_length=300, widget=forms.TextInput(attrs={
        'id': 'address',
        'placeholder': 'المدينة - الحي - الشارع',
        'required': True
    }))
    store_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'storeName',
        'placeholder': 'مثال: متجر النخبة',
        'required': True
    }))
    store_category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'id': 'storeCategory',
        'list': 'storeCats',
        'placeholder': 'مثال: إلكترونيات / ملابس / عطور...',
        'required': True
    }))
    rating = forms.DecimalField(max_digits=2, decimal_places=1, widget=forms.NumberInput(attrs={
        'id': 'rating',
        'list': 'ratings',
        'placeholder': 'مثال: 4.5',
        'required': True
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'id': 'phone',
        'placeholder': '+963 9xx xxx xxx'
    }))

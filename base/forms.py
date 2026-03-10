from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import StoreCategory, OTPCode
from utils.validators import SyrianPhoneValidator
from utils.types import UserType

User = get_user_model()

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

class VendorSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'fullName', 'placeholder': 'مثال: أحمد خالد', 'required': True
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'email', 'placeholder': 'name@example.com', 'required': True
    }))
    address = forms.CharField(max_length=300, widget=forms.TextInput(attrs={
        'id': 'address', 'placeholder': 'المدينة - الحي - الشارع', 'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'password', 'placeholder': '••••••••', 'required': True
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'confirm_password', 'placeholder': '••••••••', 'required': True
    }))
    store_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'storeName', 'placeholder': 'مثال: متجر النخبة', 'required': True
    }))
    store_category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'id': 'storeCategory', 'list': 'storeCats', 'placeholder': 'مثال: إلكترونيات / ملابس / عطور...', 'required': True
    }))
    phone = forms.CharField(
        max_length=20, 
        required=False, 
        validators=[SyrianPhoneValidator()],
        widget=forms.TextInput(attrs={'id': 'phone', 'placeholder': '+963 9xx xxx xxx'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("كلمات المرور غير متطابقة.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني مسجل مسبقاً.")
        return email

class BuyerSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'fullName', 'placeholder': 'مثال: أحمد خالد', 'required': True
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'email', 'placeholder': 'name@example.com', 'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'password', 'placeholder': '••••••••', 'required': True
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'confirm_password', 'placeholder': '••••••••', 'required': True
    }))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("كلمات المرور غير متطابقة.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني مسجل مسبقاً.")
        return email

class OTPForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'email', 'placeholder': 'name@example.com', 'required': True
    }))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if OTPCode.check_limit(email):
            raise ValidationError("لقد تجاوزت الحد المسموح به من طلبات الرمز. يرجى المحاولة لاحقاً.")
        
        if not User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني غير مسجل لدينا.")
            
        return email

class VerifyOTPForm(forms.Form):
    code = forms.IntegerField(widget=forms.NumberInput(attrs={
        'id': 'otpCode', 'placeholder': '123456', 'required': True
    }))

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not (100000 <= code <= 999999):
            raise ValidationError("رمز التحقق يجب أن يتكون من 6 أرقام.")
        return code

class AccountUpdateForm(forms.Form):
    display_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'displayName', 'placeholder': 'الاسم المعروض'
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'id': 'accountPhone', 'placeholder': '+963 9xx xxx xxx'
    }))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'id': 'avatarInput'
    }))

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'id': 'fn', 'placeholder': 'الاسم الكامل', 'required': True
    }))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'id': 'ph', 'placeholder': '+963 9xx xxx xxx', 'required': True
    }))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'id': 'ct', 'placeholder': 'المدينة', 'required': True
    }))
    address = forms.CharField(widget=forms.Textarea(attrs={
        'id': 'adr', 'placeholder': 'العنوان التفصيلي', 'required': True
    }))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'id': 'nts', 'placeholder': 'ملاحظات إضافية'
    }))

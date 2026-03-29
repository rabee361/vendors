from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import StoreCategory, OTPCode, ContactMessage, CustomUser
from utils.validators import SyrianPhoneValidator
from utils.types import UserType
from django.contrib.auth import authenticate
from .models import Product, Offer, SponsoredAd, Order, Vendor, ProductCategory, Coupon

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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise ValidationError("خطأ في البريد الإلكتروني أو كلمة المرور.")
            if not user.is_buyer:
                raise ValidationError("هذا الحساب ليس حساب مشتري.")
            if not user.is_active:
                raise ValidationError("هذا الحساب غير مفعل.")
            cleaned_data['user'] = user
        return cleaned_data

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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            print(user)
            if not user:
                raise ValidationError("خطأ في البريد الإلكتروني أو كلمة المرور.")
            if not user.is_seller:
                raise ValidationError("هذا الحساب ليس حساب بائع.")
            if not user.is_active:
                raise ValidationError("هذا الحساب غير مفعل.")
            cleaned_data['user'] = user
        return cleaned_data

class ModeratorLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'id': 'adminEmail',
        'placeholder': 'admin@example.com',
        'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'adminPass',
        'placeholder': '••••••••',
        'required': True
    }))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise ValidationError("خطأ في البريد الإلكتروني أو كلمة المرور.")
            if user.user_type != 'admin':
                raise ValidationError("هذا الحساب ليس حساب مسؤول.")
            cleaned_data['user'] = user
        return cleaned_data

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
    store_category = forms.CharField(max_length=100, widget=forms.Select(attrs={
        'id': 'storeCategory', 'required': True
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
    email = forms.EmailField(label='البريد الإلكتروني', widget=forms.EmailInput(attrs={
        'id': 'email', 'placeholder': 'البريد الإلكتروني', 'required': True
    }))
    full_name = forms.CharField(label='الاسم الكامل', max_length=150, widget=forms.TextInput(attrs={
        'id': 'fn', 'placeholder': 'الاسم الكامل', 'required': True
    }))
    phone = forms.CharField(label='رقم الهاتف', max_length=20,validators=[SyrianPhoneValidator()], widget=forms.TextInput(attrs={
        'id': 'ph', 'placeholder': '+963 9xx xxx xxx', 'required': True
    }))
    city = forms.CharField(label='المدينة', max_length=100, widget=forms.TextInput(attrs={
        'id': 'ct', 'placeholder': 'المدينة', 'required': True
    }))
    address = forms.CharField(label='العنوان التفصيلي', widget=forms.Textarea(attrs={
        'id': 'adr', 'placeholder': 'العنوان التفصيلي', 'required': True
    }))
    notes = forms.CharField(label='ملاحظات إضافية (اختياري)', required=False, widget=forms.Textarea(attrs={
        'id': 'nts', 'placeholder': 'ملاحظات إضافية'
    }))


class MessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'name', 'placeholder': 'الاسم الكامل', 'required': True
            }),
            'email': forms.EmailInput(attrs={
                'id': 'email', 'placeholder': 'name@example.com', 'required': True
            }),
            'message': forms.Textarea(attrs={
                'id': 'message', 'placeholder': 'الرسالة', 'required': True
            })
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = StoreCategory
        fields = ['name', 'slug', 'description']

class MessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'message', 'email']


class ModeratorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'avatar']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and password != confirm_password:
            raise forms.ValidationError("كلمات المرور غير متطابقة.")
        return cleaned_data


class ModeratorVendorForm(forms.ModelForm):
    is_active = forms.BooleanField(required=False)
    class Meta:
        model = Vendor
        fields = ['store_name', 'category', 'address', 'phone', 'logo','is_active']

    def save(self, commit=True):
        vendor = super().save(commit=False)
        vendor.user.is_active = self.cleaned_data['is_active']
        if commit:
            vendor.save()
            vendor.user.save()
        return vendor

class ProductForm(forms.ModelForm):
    send_notification = forms.BooleanField(
        required=False,
        label='إرسال إشعار بريدي للعملاء الذين استلموا طلباتهم',
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields.pop('send_notification', None)

        if vendor:
            self.fields['category'].queryset = ProductCategory.objects.filter(tenant=vendor)

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'اسم المنتج'}),
            'description': forms.Textarea(attrs={'placeholder': 'وصف المنتج'}),
            'price': forms.NumberInput(attrs={'placeholder': 'السعر'}),
            'stock': forms.NumberInput(attrs={'placeholder': 'المخزون'}),
            'category': forms.Select(),
        }

class OfferForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['product'].queryset = Product.objects.filter(tenant=vendor)

    class Meta:
        model = Offer
        fields = ['product', 'discount', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SponsoredAdForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['product'].queryset = Product.objects.filter(tenant=vendor)

    class Meta:
        model = SponsoredAd
        fields = ['ad_type', 'product', 'status', 'end_date']
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status','shipping_cost']
        widgets = {
            'shipping_cost': forms.NumberInput(attrs={'placeholder': 'تكلفة الشحن'}),
        }

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name','description','slug']

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="كلمة المرور القديمة", widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}), required=True)
    new_password = forms.CharField(label="كلمة المرور الجديدة", widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}), required=True)
    confirm_password = forms.CharField(label="تأكيد كلمة المرور الجديدة", widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}), required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if self.user and old_password:
            if not self.user.check_password(old_password):
                raise forms.ValidationError("كلمة المرور القديمة غير صحيحة.")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("كلمات المرور الجديدة غير متطابقة.")
            
        if old_password and new_password and old_password == new_password:
            raise forms.ValidationError("كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة.")
            
        return cleaned_data

    def save(self):
        new_password = self.cleaned_data.get("new_password")
        self.user.set_password(new_password)
        self.user.save()
        return self.user

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['value', 'start_date', 'end_date','orders_to_receive']
        widgets = {
            
            'value': forms.NumberInput(attrs={'placeholder': 'قيمة الخصم الثابتة$'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class VendorSettingsForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['store_name', 'address', 'phone', 'logo']
        widgets = {
            'store_name': forms.TextInput(attrs={'placeholder': 'اسم المتجر'}),
            'address': forms.TextInput(attrs={'placeholder': 'المدينة - الحي - الشارع'}),
            'phone': forms.TextInput(attrs={'placeholder': '+963 9xx xxx xxx'}),
        }

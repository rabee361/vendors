from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from utils.helper import generate_code, get_expiration_time
from utils.types import UserType, AdType, AdStatus, OrderStatus, CodeTypes
from django.utils import timezone
from utils.managers import CustomUserManager
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.BUYER)
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=140,unique=True)
    is_verified = models.BooleanField(default=False)

    @property
    def is_buyer(self):
        return self.user_type == UserType.BUYER

    @property
    def is_seller(self):
        return self.user_type == UserType.SELLER

    @property
    def is_page_admin(self):
        return self.user_type == UserType.ADMIN

    def clean(self):
        if self.avatar and self.avatar.size > 2 * 1024 * 1024:  # 2MB in bytes
            raise ValidationError('حجم الصورة يجب أن لا يتجاوز 2 ميجابايت')

        if self.avatar and not self.avatar.name.endswith(('.jpg', '.jpeg', '.png','webp', 'jfif')):
            raise ValidationError('يجب أن يكون الصورة بصيغة jpg أو jpeg أو png أو webp')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def create_otp(self, code_type=CodeTypes.SIGNUP):
        # Delete old unused codes of the same type for this email
        OTPCode.objects.filter(email=self.email, code_type=code_type, is_used=False).delete()
        
        otp = OTPCode.objects.create(
            code_type=code_type,
            email=self.email,
        )
        return otp.code

class Buyer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='buyer_profile')
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Buyer: {self.user.username}"

class Vendor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='vendor_profile')
    store_name = models.CharField(max_length=150)
    category = models.ForeignKey('StoreCategory', on_delete=models.SET_NULL, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='vendors/avatars/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name

class ProductCategory(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='product_categories')
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Product Categories"

class StoreCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/images/', blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/images/')
    is_active = models.BooleanField(default=True)
    is_sponsored_badge = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, allow_unicode=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Offer(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='offers', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    discount = models.PositiveIntegerField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def discount_price(self):
        return f"{self.original_price - (self.original_price * self.discount / 100):.2f}"

    def __str__(self):
        return f"{self.discount}% off {self.product.name}"

class SponsoredAd(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='ads')
    ad_type = models.CharField(max_length=20, choices=AdType.choices)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    days_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=AdStatus.choices, default=AdStatus.PENDING)
    start_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ad for {self.product.name} ({self.ad_type})"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} ({self.user or self.session_key})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('preparing', 'قيد التجهيز'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='order_items')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"

class VendorStats(models.Model):
    tenant = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='stats')
    week_start = models.DateField()
    views = models.PositiveIntegerField(default=0)
    sales_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    visit_growth = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    best_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stats for {self.tenant.store_name} - {self.week_start}"


class OTPCode(models.Model):
    email = models.EmailField(max_length=255)
    code = models.IntegerField(validators=[MinValueValidator(100000), MaxValueValidator(999999)], default=generate_code)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_expiration_time)
    code_type = models.CharField(max_length=20, choices=CodeTypes.choices, default=CodeTypes.SIGNUP)
    is_used = models.BooleanField(default=False)

    @staticmethod
    def check_limit(email):
        return OTPCode.objects.filter(
            email=email,
            created_at__gt=timezone.now() - timezone.timedelta(minutes=15)
        ).count() >= 5

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        return f"{self.email} - {self.code} ({self.code_type})"

from django.db import models

class UserType(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'
    ADMIN = 'admin', 'Admin'

class AdType(models.TextChoices):
    SECTION = 'section', 'قسم الإعلانات الممولة'
    BADGE = 'badge', 'وسم ممول على الصورة'

class AdStatus(models.TextChoices):
    ACTIVE = 'active', 'نشط'
    PENDING = 'pending', 'قيد المراجعة'
    EXPIRED = 'expired', 'منتهي'
    REJECTED = 'rejected', 'مرفوض'

class OrderStatus(models.TextChoices):
    PREPARING = 'preparing', 'قيد التجهيز'
    SHIPPED = 'shipped', 'تم الشحن'
    DELIVERED = 'delivered', 'تم التسليم'
    CANCELLED = 'cancelled', 'ملغي'

class CodeTypes(models.TextChoices):
    SIGNUP = 'SIGNUP'
    RESET_PASSWORD = 'RESET_PASSWORD'
    FORGET_PASSWORD = 'FORGET_PASSWORD'

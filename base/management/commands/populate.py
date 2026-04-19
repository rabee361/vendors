import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.conf import settings
from base.models import (
    Buyer, Vendor, StoreCategory, ProductCategory, Product, 
    Offer, SponsoredAd, Cart, CartItem, Favorite, Order, 
    OrderItem, ContactMessage, VendorStats, OTPCode, Setting
)
from utils.types import UserType, AdType, AdStatus, CodeTypes
import os
from datetime import date, timedelta

User = get_user_model()

# logical hardcoded data
STORE_CATEGORIES = ["الإلكترونيات", "الأزياء", "المنزل والمطبخ", "الصحة والجمال", "الرياضة والرحلات"]
COMPANY_NAMES = ["تقنية النخبة", "ستايل المدينة", "نقاء الجمال", "قمة الأداء", "بيت الراحة", "سوق السرعة", "الواحة الخضراء"]
PRODUCT_NAMES = {
    "الإلكترونيات": [
        "حاسوب محمول",
        "سماعات لاسلكية",
        "ساعة ذكية",
        "شاشة 4K",
        "مكبر صوت بلوتوث",
        "هاتف ذكي",
        "جهاز لوحي",
        "كاميرا رقمية",
        "لوحة مفاتيح ميكانيكية",
        "فأرة ألعاب",
    ],
    "الأزياء": [
        "قميص بتصميم عصري",
        "جاكيت جلدي",
        "حذاء رياضي",
        "وشاح حريري",
        "بنطال جينز",
        "فستان أنيق",
        "حقيبة يد",
        "نظارة شمسية",
        "عباية عملية",
        "قميص كاجوال",
    ],
    "المنزل والمطبخ": [
        "آلة تحضير القهوة",
        "قلاية هوائية",
        "طقم سكاكين",
        "وسادة ميموري فوم",
        "مصباح ذكي",
        "خلاط كهربائي",
        "طاولة جانبية",
        "طقم قدور",
        "مفرش طاولة",
        "مكنسة كهربائية",
    ],
    "الصحة والجمال": [
        "سيروم للوجه",
        "فرشاة أسنان كهربائية",
        "سجادة يوغا",
        "مجفف شعر",
        "طقم طلاء أظافر",
        "كريم ترطيب",
        "عطر ناعم",
        "ماكينة حلاقة",
        "غسول للبشرة",
        "جهاز مساج",
    ],
    "الرياضة والرحلات": [
        "خيمة رحلات",
        "طقم دمبل",
        "دراجة جبلية",
        "حذاء للمشي",
        "مضرب تنس",
        "حقيبة ظهر",
        "زجاجة رياضية",
        "كرة قدم",
        "جهاز تمارين منزلي",
        "كرسي تخييم",
    ],
}
PRODUCT_VARIANTS = ["برو", "ماكس", "بلس", "ألترا", "إير", "إكس", "سمارت", "إصدار حديث", "إصدار فاخر", "إصدار عملي"]
DEFAULT_PRODUCT_NAMES = ["منتج مميز", "منتج عملي", "منتج عصري"]
VENDOR_CATEGORY_NAMES = ["الأساسيات", "وصل حديثاً", "الأكثر مبيعاً"]
CITIES = ["بغداد", "أربيل", "البصرة", "الموصل", "السليمانية", "دهوك", "كركوك"]
DESCRIPTIONS = [
    "جودة عالية ومتانة ممتازة للاستخدام طويل الأمد.",
    "تصميم عصري للاستخدام اليومي مع خامات مختارة بعناية.",
    "قيمة ممتازة مقابل السعر مع أداء موثوق ومميز.",
    "إصدار محدود يناسب من يبحث عن القطع المميزة.",
    "مزايا عملية تمنح راحة وكفاءة في الاستخدام اليومي."
]
ORDER_NOTES = ["يرجى الاتصال قبل التوصيل", "اترك الطلب عند الباب", "يرجى التعامل بحذر", None]
CONTACT_MESSAGES = [
    "لدي استفسار بخصوص طلبي الأخير. هل يمكنكم المساعدة؟",
    "أرغب في معرفة موعد التوصيل المتوقع لهذا المنتج.",
    "هل هذا المنتج متوفر بألوان أو مقاسات أخرى؟",
]
AD_SETTINGS = {
    'ad_click_cost': '5',
    'minimum_ad_budget': '15',
    'normal_ads_budget': '25',
}


def random_decimal(min_value, max_value, places=2):
    return Decimal(str(round(random.uniform(min_value, max_value), places)))


def generate_unique_product_name(store_category_name, used_names):
    base_names = PRODUCT_NAMES.get(store_category_name, DEFAULT_PRODUCT_NAMES)
    candidates = list(base_names)
    candidates.extend(
        f"{base_name} {variant}"
        for base_name in base_names
        for variant in PRODUCT_VARIANTS
    )
    random.shuffle(candidates)

    for candidate in candidates:
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

    fallback_index = 1
    while True:
        candidate = f"{random.choice(base_names)} إصدار خاص {fallback_index}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        fallback_index += 1

class Command(BaseCommand):
    help = 'Populate the database with fake data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Populating database...")

        # 0. Create sponsored ad settings
        self.stdout.write("Generating Settings...")
        for name, value in AD_SETTINGS.items():
            Setting.objects.update_or_create(
                name=name,
                defaults={'value': value},
            )

        sponsored_ad_settings = Setting.get_sponsored_ad_settings()

        # 1. Create Store Categories
        self.stdout.write("Generating Store Categories...")
        store_categories = []
        for name in STORE_CATEGORIES:
            cat, created = StoreCategory.objects.get_or_create(
                name=name,
                defaults={'description': random.choice(DESCRIPTIONS)}
            )
            store_categories.append(cat)

        # 2. Create Users (Buyers, Sellers, Admins)
        self.stdout.write("Generating Users...")
        
        # Admin
        self.stdout.write("Generating Admins...")
        
        # Default Super User
        admin_email = 'admin@admin.admin'
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin'
            )
            self.stdout.write(self.style.SUCCESS(f"Created default superuser: {admin_email}"))

        # Other Admins
        for i in range(2):
            email = f"admin_{i}@honeybunny.online"
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    username=email,
                    email=email,
                    password='password123',
                    user_type=UserType.ADMIN
                )

        # 3. Create Vendors (Sellers)
        self.stdout.write("Generating Vendors...")
        vendors = []
        placeholder_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'placeholder.jfif')
        
        for i in range(5):
            email = f"seller_{i}@honeybunny.online"
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password='password123',
                    user_type=UserType.SELLER
                )
            else:
                user = User.objects.get(username=email)
            
            vendor, created = Vendor.objects.get_or_create(
                user=user,
                defaults={
                    'store_name': COMPANY_NAMES[i % len(COMPANY_NAMES)],
                    'category': random.choice(store_categories),
                    'address': f"{random.choice(CITIES)}، شارع {random.randint(1, 100)}",
                    'phone': f"+9647{random.randint(700000000, 799999999)}",
                }
            )
            
            if created and os.path.exists(placeholder_path):
                with open(placeholder_path, 'rb') as f:
                    vendor.logo.save('avatar.jfif', File(f), save=True)
            
            vendors.append(vendor)

        # 4. Create Buyers
        self.stdout.write("Generating Buyers...")
        buyers = []
        for i in range(8):
            email = f"buyer_{i}@example.com"
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password='password123',
                    user_type=UserType.BUYER
                )
            else:
                user = User.objects.get(username=email)
            
            buyer, created = Buyer.objects.get_or_create(
                user=user,
                defaults={'address': f"{random.choice(CITIES)}، حي {random.randint(1, 20)}"}
            )
            buyers.append(buyer)

        # 5. Create Product Categories and Products
        self.stdout.write("Generating Products and Categories...")
        all_products = []
        used_product_names = set(Product.objects.values_list('name', flat=True))
        for idx, vendor in enumerate(vendors):
            # Create a few categories per vendor
            vendor_cats = VENDOR_CATEGORY_NAMES
            for cat_name in vendor_cats:
                p_cat, created = ProductCategory.objects.get_or_create(
                    tenant=vendor,
                    name=f"{vendor.store_name} {cat_name}",
                    defaults={'description': f"منتجات {cat_name} من متجر {vendor.store_name}"}
                )
                
                # Fetch product names based on vendor's store category
                store_cat_name = vendor.category.name if vendor.category else None
                
                for i in range(random.randint(3, 6)):
                    prod_name = generate_unique_product_name(store_cat_name, used_product_names)
                    product, created = Product.objects.get_or_create(
                        tenant=vendor,
                        name=prod_name,
                        defaults={
                            'description': random.choice(DESCRIPTIONS),
                            'price': random_decimal(15, 450),
                            'stock': random.randint(10, 200),
                            'category': p_cat,
                            'is_active': True
                        }
                    )
                    
                    if created and os.path.exists(placeholder_path):
                        with open(placeholder_path, 'rb') as f:
                            product.image.save('placeholder.jfif', File(f), save=True)
                    
                    all_products.append(product)

        # 6. Create Offers
        self.stdout.write("Generating Offers...")
        for vendor in vendors:
            vendor_products = [p for p in all_products if p.tenant == vendor]
            if vendor_products:
                for _ in range(random.randint(1, 2)):
                    prod = random.choice(vendor_products)
                    Offer.objects.get_or_create(
                        product=prod,
                        defaults={
                            'tenant': vendor,
                            'discount': random.randint(10, 40),
                            'start_date': date.today(),
                            'end_date': date.today() + timedelta(days=random.randint(7, 30)),
                            'is_active': True
                        }
                    )

          # 7. Create Sponsored Ads
        
        self.stdout.write("Generating Ads...")
        if all_products:
            for _ in range(5):
                      product = random.choice(all_products)
                      ad_type = random.choice(AdType.values)
                      if ad_type == AdType.BADGE:
                          budget = sponsored_ad_settings['normal_ads_budget']
                      else:
                          budget = random.randint(
                                sponsored_ad_settings['minimum_ad_budget'],
                                sponsored_ad_settings['minimum_ad_budget'] + 50,
                          )

                      SponsoredAd.objects.create(
                    tenant=product.tenant,
                          ad_type=ad_type,
                    product=product,
                          budget=budget,
                    status=AdStatus.ACTIVE,
                    end_date=date.today() + timedelta(days=random.randint(7, 30))
                )

        # 8. Create Carts and Favorites
        self.stdout.write("Generating Favorites and Carts...")
        buyer_users = [b.user for b in buyers]
        for user in buyer_users:
            # Favorites
            if all_products:
                fav_prods = random.sample(all_products, k=min(len(all_products), random.randint(1, 3)))
                for p in fav_prods:
                    Favorite.objects.get_or_create(user=user, product=p)
            
            # Cart
            cart, created = Cart.objects.get_or_create(user=user)
            if all_products and created:
                cart_prods = random.sample(all_products, k=min(len(all_products), random.randint(1, 2)))
                for p in cart_prods:
                    CartItem.objects.create(cart=cart, product=p, quantity=random.randint(1, 2))

        # 9. Create Orders
        self.stdout.write("Generating Orders...")
        for i in range(10):
            vendor = random.choice(vendors)
            order_num = f"ORD-{random.randint(10000, 99999)}"
            shipping = random_decimal(5, 15)
            
            order = Order.objects.create(
                tenant=vendor,
                order_number=order_num,
                total=0,
                full_name=f"العميل {i + 1}",
                email=f"customer_{i}@example.com",
                phone=f"+9639{random.randint(30000000, 99999999)}",
                city=random.choice(CITIES),
                address=f"شارع {random.randint(1, 50)}، منزل {random.randint(1, 100)}",
                notes=random.choice(ORDER_NOTES),
                shipping_cost=shipping,
                status='preparing'
            )
            
            order_total = 0
            vendor_prods = [p for p in all_products if p.tenant == vendor]
            if vendor_prods:
                items_to_add = random.sample(vendor_prods, k=min(len(vendor_prods), random.randint(1, 2)))
                for p in items_to_add:
                    qty = random.randint(1, 2)
                    price = p.price
                    OrderItem.objects.create(
                        tenant=vendor,
                        order=order,
                        product=p,
                        quantity=qty,
                        price_at_order=price
                    )
                    order_total += (price * qty)
            
            order.total = order_total + shipping
            order.save()

        # 10. Messages and Stats
        self.stdout.write("Generating Messages and Stats...")
        for vendor in vendors:
            # Stats
            VendorStats.objects.get_or_create(
                tenant=vendor,
                week_start=date.today() - timedelta(days=7),
                defaults={
                    'views': random.randint(200, 800),
                    'sales_total': random_decimal(500, 2000),
                    'conversion_rate': random_decimal(2, 8),
                    'visit_growth': random_decimal(0, 10)
                }
            )
            
            # Messages
            ContactMessage.objects.create(
                name=f"العميل {random.randint(1, 100)}",
                email=f"customer{random.randint(1, 100)}@example.com",
                message=random.choice(CONTACT_MESSAGES),
            )

        # 11. OTP Codes
        self.stdout.write("Generating OTPs...")
        for i in range(5):
            OTPCode.objects.create(
                email=f"test_user_{i}@example.com",
                code_type=random.choice(CodeTypes.values)
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))

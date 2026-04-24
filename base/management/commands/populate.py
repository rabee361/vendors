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
PRODUCT_CATEGORY_SEEDS = {
    "الإلكترونيات": [
        {
            "name": "إلكترونيات",
            "products": [
                ("هاتف", "للتواصل والتنقل اليومي", ["الشاحن", "السماعة", "الحقيبة", "السفر"]),
                ("حاسوب", "للعمل والدراسة", ["الطاولة", "الحقيبة", "الشاحن", "المكتب"]),
                ("جهاز تتبع", "لمتابعة الموقع وحفظ المسار", ["الحقيبة", "الدراجة", "السيارة", "الرحلات"]),
                ("كاميرا", "لتوثيق الرحلات والمشاوير", ["حقيبة الظهر", "الخيمة", "الدراجة", "السفر"]),
            ],
        },
        {
            "name": "صوتيات",
            "products": [
                ("سماعة", "للاستماع أثناء العمل أو المشي", ["الهاتف", "الحاسوب", "الحقيبة", "السفر"]),
                ("مكبر صوت", "لتشغيل الصوت في المنزل أو الرحلات", ["الهاتف", "الخيمة", "الجلسات", "المنزل"]),
                ("ميكروفون", "للتسجيل والمكالمات", ["الحاسوب", "الهاتف", "العمل", "الدراسة"]),
                ("راديو", "لمتابعة الصوت أثناء التنقل", ["الرحلات", "الخيمة", "المصباح", "السفر"]),
            ],
        },
        {
            "name": "ملحقات",
            "products": [
                ("شاحن", "لشحن الأجهزة في البيت أو الطريق", ["الهاتف", "الحاسوب", "السيارة", "السفر"]),
                ("كابل", "لتوصيل الأجهزة ونقل الطاقة", ["الشاحن", "الهاتف", "الحاسوب", "المكتب"]),
                ("لوحة مفاتيح", "للكتابة والعمل", ["الحاسوب", "الطاولة", "المكتب", "الدراسة"]),
                ("فأرة", "للتحكم اليومي على المكتب", ["الحاسوب", "لوحة المفاتيح", "الطاولة", "العمل"]),
            ],
        },
        {
            "name": "متفرقات",
            "products": [
                ("بطارية", "لتغذية الأجهزة الصغيرة عند التنقل", ["جهاز التتبع", "المصباح", "الحقيبة", "الرحلات"]),
                ("حامل", "لتثبيت الهاتف أو الكاميرا", ["الدراجة", "السيارة", "الهاتف", "الرحلات"]),
                ("مصباح", "للإضاءة في البيت أو التخييم", ["الخيمة", "الحقيبة", "الطاولة", "الرحلات"]),
            ],
        },
    ],
    "الأزياء": [
        {
            "name": "ملابس",
            "products": [
                ("قميص", "للاستخدام اليومي والعمل", ["البنطال", "الحذاء", "الحقيبة", "الساعة"]),
                ("بنطال", "للاستخدام اليومي والتنقل", ["القميص", "الحذاء", "الحقيبة", "المشي"]),
                ("فستان", "للاستخدام اليومي والمناسبات", ["الحقيبة", "الحذاء", "الساعة", "العطر"]),
                ("عباية", "للاستخدام اليومي والخروج", ["الحقيبة", "الحذاء", "العطر", "الساعة"]),
            ],
        },
        {
            "name": "أحذية",
            "products": [
                ("حذاء", "للمشي والخروج اليومي", ["القميص", "البنطال", "الحقيبة", "الرحلات"]),
                ("صندل", "للاستخدام الخفيف", ["الفستان", "الحقيبة", "المشاوير", "الصيف"]),
                ("جزمة", "للحركة في الطريق والطقس البارد", ["البنطال", "المظلة", "الحقيبة", "الخروج"]),
                ("شبشب", "للاستخدام المنزلي واليومي", ["المنزل", "الحمام", "الراحة", "المنشفة"]),
            ],
        },
        {
            "name": "حقائب",
            "products": [
                ("حقيبة", "لحمل الأغراض اليومية", ["القميص", "الساعة", "الهاتف", "الخروج"]),
                ("محفظة", "لحفظ النقود والبطاقات", ["الحقيبة", "الهاتف", "الخروج", "السفر"]),
                ("حقيبة ظهر", "للجامعة والعمل والرحلات", ["جهاز التتبع", "الزجاجة", "الدراجة", "السفر"]),
                ("حافظة", "لحفظ المستلزمات الصغيرة", ["الحقيبة", "الفرشاة", "الشاحن", "السفر"]),
            ],
        },
        {
            "name": "متفرقات",
            "products": [
                ("حزام", "لتنسيق اللبس اليومي", ["القميص", "البنطال", "الحذاء", "الخروج"]),
                ("ساعة", "لمتابعة الوقت أثناء العمل والتنقل", ["القميص", "الحقيبة", "الهاتف", "السفر"]),
                ("نظارة", "للاستخدام اليومي في الطريق", ["الحقيبة", "القبعة", "السفر", "الخروج"]),
            ],
        },
    ],
    "المنزل والمطبخ": [
        {
            "name": "مطبخ",
            "products": [
                ("آلة قهوة", "لتحضير المشروبات في البيت أو المكتب", ["الكوب", "الطاولة", "العمل", "المنزل"]),
                ("خلاط", "لتحضير الطعام والمشروبات", ["المطبخ", "الطعام", "الكوب", "المنزل"]),
                ("قلاية", "لطهي الوجبات اليومية", ["المطبخ", "الطعام", "المنزل", "التخزين"]),
                ("قدر", "لطهي الطعام في البيت أو الرحلات", ["المطبخ", "الخيمة", "الطعام", "الرحلات"]),
            ],
        },
        {
            "name": "منزل",
            "products": [
                ("وسادة", "للراحة في البيت أو السفر", ["السرير", "الحقيبة", "الرحلات", "الراحة"]),
                ("مصباح", "للإضاءة على الطاولة أو قرب السرير", ["الطاولة", "البيت", "الخيمة", "الرحلات"]),
                ("طاولة", "للعمل أو تناول الطعام", ["الحاسوب", "آلة القهوة", "المنزل", "المكتب"]),
                ("مكنسة", "لتنظيف البيت بشكل يومي", ["المنزل", "السلة", "التنظيم", "الراحة"]),
            ],
        },
        {
            "name": "أثاث",
            "products": [
                ("كرسي", "للجلوس في البيت أو المكتب", ["الطاولة", "الحاسوب", "العمل", "الراحة"]),
                ("رف", "لترتيب الأدوات والكتب", ["المنظم", "الصندوق", "المنزل", "المكتب"]),
                ("صندوق", "لتخزين الأغراض اليومية", ["المنظم", "الحقيبة", "المنزل", "الرحلات"]),
                ("مرآة", "للاستخدام اليومي في المنزل", ["الفرشاة", "العطر", "التجميل", "المنزل"]),
            ],
        },
        {
            "name": "متفرقات",
            "products": [
                ("ترمس", "لحفظ المشروبات أثناء العمل أو الرحلات", ["القهوة", "الزجاجة", "الخيمة", "السفر"]),
                ("سلة", "لترتيب الأغراض في البيت", ["المنظم", "المكنسة", "المنزل", "التخزين"]),
                ("منظم", "لتجميع الأدوات الصغيرة", ["الصندوق", "الحقيبة", "المكتب", "الرحلات"]),
            ],
        },
    ],
    "الصحة والجمال": [
        {
            "name": "عناية",
            "products": [
                ("كريم", "للعناية اليومية بالبشرة", ["الغسول", "المرآة", "الحقيبة", "السفر"]),
                ("غسول", "للتنظيف اليومي", ["الكريم", "المنشفة", "المرآة", "الحمام"]),
                ("شامبو", "للعناية بالشعر", ["المنشفة", "المجفف", "الحقيبة", "السفر"]),
                ("صابون", "للاستخدام اليومي في البيت أو الرحلات", ["الغسول", "المنشفة", "الحقيبة", "الرحلات"]),
            ],
        },
        {
            "name": "تجميل",
            "products": [
                ("فرشاة", "لترتيب الشعر أو أدوات التجميل", ["المرآة", "الحقيبة", "المجفف", "السفر"]),
                ("مرآة", "للاستخدام اليومي أثناء الترتيب", ["الفرشاة", "العطر", "الحقيبة", "الخروج"]),
                ("مجفف شعر", "لتجفيف الشعر في البيت أو السفر", ["الفرشاة", "الحقيبة", "الشامبو", "السفر"]),
                ("طلاء أظافر", "للعناية اليومية البسيطة", ["المرآة", "الحقيبة", "الخروج", "التجميل"]),
            ],
        },
        {
            "name": "عطور",
            "products": [
                ("عطر", "للاستخدام اليومي والخروج", ["الحقيبة", "المرآة", "الفستان", "القميص"]),
                ("بخاخ", "للانتعاش السريع أثناء اليوم", ["الحقيبة", "السفر", "الخروج", "العمل"]),
                ("زيت", "للعناية بالجسم أو الشعر", ["الشامبو", "الكريم", "المنشفة", "الحمام"]),
                ("لوشن", "للترطيب بعد العناية اليومية", ["الكريم", "الغسول", "المنشفة", "السفر"]),
            ],
        },
        {
            "name": "متفرقات",
            "products": [
                ("ماكينة حلاقة", "للعناية الشخصية في البيت أو السفر", ["المرآة", "الحقيبة", "المنشفة", "السفر"]),
                ("جهاز مساج", "للراحة بعد العمل أو الرياضة", ["الدمبل", "سجادة اليوغا", "الراحة", "المنزل"]),
                ("منشفة", "للاستخدام اليومي بعد العناية أو الرحلات", ["الغسول", "الشامبو", "الحقيبة", "السفر"]),
            ],
        },
    ],
    "الرياضة والرحلات": [
        {
            "name": "رياضة",
            "products": [
                ("كرة", "للتمرين واللعب اليومي", ["الحذاء", "الملعب", "الحقيبة", "الخروج"]),
                ("دمبل", "للتمرين في البيت أو النادي", ["جهاز المساج", "الزجاجة", "الرياضة", "المنزل"]),
                ("جهاز تمارين", "للتمرين المنتظم", ["الدمبل", "الزجاجة", "المنزل", "اللياقة"]),
                ("حبل", "للتمرين السريع في البيت أو الحديقة", ["الحذاء", "الرياضة", "الزجاجة", "الخروج"]),
            ],
        },
        {
            "name": "رحلات",
            "products": [
                ("خيمة", "للتخييم والرحلات الطويلة", ["المصباح", "الزجاجة", "القدر", "جهاز التتبع"]),
                ("زجاجة", "لحمل الماء أثناء المشي أو الرياضة", ["حقيبة الظهر", "الدراجة", "الرحلات", "التمرين"]),
                ("بوصلة", "لتحديد الاتجاه أثناء الرحلات", ["الخيمة", "الحقيبة", "جهاز التتبع", "السفر"]),
                ("كرسي تخييم", "للجلوس في الرحلات", ["الخيمة", "المصباح", "الترمس", "الرحلات"]),
            ],
        },
        {
            "name": "معدات",
            "products": [
                ("دراجة", "للتنقل والرياضة في نفس الوقت", ["جهاز التتبع", "الزجاجة", "الحامل", "الرحلات"]),
                ("مضرب", "للعب والتمرين في النادي أو الحديقة", ["الكرة", "الحقيبة", "الخروج", "الرياضة"]),
                ("حقيبة ظهر", "لحمل الأدوات في المشي والرحلات", ["جهاز التتبع", "الزجاجة", "الخيمة", "السفر"]),
                ("حذاء مشي", "للمشي والرحلات اليومية", ["الحقيبة", "الزجاجة", "الدراجة", "الخروج"]),
            ],
        },
        {
            "name": "متفرقات",
            "products": [
                ("قفل", "لتأمين الحقيبة أو الدراجة", ["جهاز التتبع", "الدراجة", "حقيبة الظهر", "السفر"]),
                ("مصباح", "للإضاءة أثناء التخييم أو الطريق", ["الخيمة", "الحقيبة", "الرحلات", "السفر"]),
                ("حامل", "لتثبيت الزجاجة أو الهاتف أثناء الحركة", ["الدراجة", "الهاتف", "الرحلات", "التمرين"]),
            ],
        },
    ],
}
DEFAULT_PRODUCT_CATEGORY_SEEDS = [
    {
        "name": "منتجات",
        "products": [
            ("منتج", "للاستخدام اليومي", ["المنزل", "الحقيبة", "العمل", "السفر"]),
            ("أداة", "للاستخدام العملي", ["التنظيم", "المنزل", "المكتب", "الرحلات"]),
            ("مستلزم", "للاحتياجات الأساسية", ["الحقيبة", "المنزل", "السفر", "الخروج"]),
        ],
    },
    {
        "name": "متفرقات",
        "products": [
            ("قطعة", "للاستخدام المتنوع", ["الحقيبة", "المنزل", "المكتب", "السفر"]),
            ("جهاز", "للاستخدام اليومي", ["المنزل", "الرحلات", "العمل", "الخروج"]),
            ("منظم", "لترتيب الأدوات الصغيرة", ["الحقيبة", "المكتب", "المنزل", "السفر"]),
        ],
    },
]
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


def generate_unique_name(base_name, used_names):
    if base_name not in used_names:
        used_names.add(base_name)
        return base_name

    fallback_index = 1
    while True:
        candidate = f"{base_name} {fallback_index}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        fallback_index += 1


def join_arabic_list(values):
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} و{values[1]}"
    return f"{'، '.join(values[:-1])}، و{values[-1]}"


def normalize_seed_product_name(product_name):
    name_parts = product_name.rsplit(" ", 1)
    if len(name_parts) == 2 and name_parts[1].isdigit():
        return name_parts[0]
    return product_name


def build_product_description(product_name, purpose, related_terms):
    base_name = normalize_seed_product_name(product_name)
    related_text = join_arabic_list(related_terms[:2])
    description_parts = [
        f"{base_name} خيار عملي ومريح للاستخدام اليومي.",
        f"وهو مناسب {purpose}.",
    ]

    if related_text:
        description_parts.append(f"ويتكامل بسهولة مع {related_text}.")

    return " ".join(description_parts)


def build_category_seeds(store_category_name, category_name_counts):
    category_seeds = PRODUCT_CATEGORY_SEEDS.get(store_category_name, DEFAULT_PRODUCT_CATEGORY_SEEDS)
    built_seeds = []

    for category_seed in category_seeds:
        base_name = category_seed["name"]
        occurrence = category_name_counts.get(base_name, 0) + 1
        category_name_counts[base_name] = occurrence

        built_seeds.append(
            {
                "name": base_name if occurrence == 1 else f"{base_name} {occurrence}",
                "description": f"منتجات {base_name}",
                "products": category_seed["products"],
            }
        )

    return built_seeds

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
        category_name_counts = {}
        for vendor in vendors:
            store_cat_name = vendor.category.name if vendor.category else None
            for category_seed in build_category_seeds(store_cat_name, category_name_counts):
                p_cat, created = ProductCategory.objects.get_or_create(
                    tenant=vendor,
                    name=category_seed['name'],
                    defaults={'description': category_seed['description']}
                )
                
                for base_name, purpose, related_terms in category_seed['products']:
                    prod_name = generate_unique_name(base_name, used_product_names)
                    product_description = build_product_description(prod_name, purpose, related_terms)
                    product, created = Product.objects.get_or_create(
                        tenant=vendor,
                        name=prod_name,
                        defaults={
                            'description': product_description,
                            'price': random_decimal(15, 450),
                            'stock': random.randint(10, 200),
                            'category': p_cat,
                            'is_active': True
                        }
                    )

                    if not created and product.description != product_description:
                        product.description = product_description
                        product.save(update_fields=['description'])
                    
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

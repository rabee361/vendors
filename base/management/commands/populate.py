import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from base.models import (
    Buyer, Vendor, StoreCategory, ProductCategory, Product, 
    Offer, SponsoredAd, Cart, CartItem, Favorite, Order, 
    OrderItem, ContactMessage, VendorStats, OTPCode
)
from utils.types import UserType, AdType, AdStatus, OrderStatus, CodeTypes
import os
from datetime import date, timedelta

User = get_user_model()

# logical hardcoded data
STORE_CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Health & Beauty", "Sports & Outdoors"]
COMPANY_NAMES = ["NexaTech", "UrbanStyle", "PureGlow", "PeakPerformance", "HomeSphere", "SwiftMart", "EcoHaven"]
PRODUCT_NAMES = {
    "Electronics": ["UltraBook Pro", "Wireless Earbuds", "Smart Watch", "4K Monitor", "BT Speaker"],
    "Fashion": ["Designer T-Shirt", "Leather Jacket", "Running Shoes", "Silk Scarf", "Denim Jeans"],
    "Home & Kitchen": ["Espresso Machine", "Air Fryer", "Chef Knife Set", "Memory Foam Pillow", "Smart Bulb"],
    "Health & Beauty": ["Face Serum", "Electric Toothbrush", "Yoga Mat", "Hair Dryer", "Nail Polish Kit"],
    "Sports & Outdoors": ["Camping Tent", "Dumbbell Set", "Mountain Bike", "Hiking Boots", "Tennis Racket"]
}
CITIES = ["Baghdad", "Erbil", "Basra", "Mosul", "Sulaymaniyah", "Duhok", "Kirkuk"]
DESCRIPTIONS = [
    "Premium quality and high durability for long-term use.",
    "Modern design for everyday use, crafted with recycled materials.",
    "Best value for your money with top-rated performance characteristics.",
    "Limited edition item, highly sought after by enthusiasts.",
    "Ergonomic features designed for maximum comfort and efficiency."
]

class Command(BaseCommand):
    help = 'Populate the database with fake data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Populating database...")

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
                    'rating': random.uniform(3.5, 5.0),
                    'address': f"{random.choice(CITIES)}, Street {random.randint(1, 100)}",
                    'phone': f"+9647{random.randint(700000000, 799999999)}",
                    'is_active': True
                }
            )
            
            if created and os.path.exists(placeholder_path):
                with open(placeholder_path, 'rb') as f:
                    vendor.avatar.save('avatar.jfif', File(f), save=True)
            
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
                defaults={'address': f"{random.choice(CITIES)}, District {random.randint(1, 20)}"}
            )
            buyers.append(buyer)

        # 5. Create Product Categories and Products
        self.stdout.write("Generating Products and Categories...")
        all_products = []
        for idx, vendor in enumerate(vendors):
            # Create a few categories per vendor
            vendor_cats = ["Essentials", "New Arrivals", "Best Sellers"]
            for cat_name in vendor_cats:
                p_cat, created = ProductCategory.objects.get_or_create(
                    tenant=vendor,
                    name=f"{vendor.store_name} {cat_name}",
                    defaults={'description': f"Selected {cat_name} from {vendor.store_name}"}
                )
                
                # Fetch product names based on vendor's store category
                store_cat_name = vendor.category.name
                available_products = PRODUCT_NAMES.get(store_cat_name, ["General Product"])
                
                for i in range(random.randint(3, 6)):
                    prod_name = f"{vendor.store_name} {random.choice(available_products)} {random.randint(1, 1000)}"
                    product, created = Product.objects.get_or_create(
                        tenant=vendor,
                        name=prod_name,
                        defaults={
                            'description': random.choice(DESCRIPTIONS),
                            'price': random.uniform(15.0, 450.0),
                            'stock': random.randint(10, 200),
                            'category': p_cat,
                            'rating': random.uniform(3.8, 5.0),
                            'rating_count': random.randint(5, 150),
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
                            'original_price': prod.price,
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
                 SponsoredAd.objects.create(
                    tenant=product.tenant,
                    ad_type=random.choice(AdType.values),
                    budget=random.uniform(100, 300),
                    days_count=random.randint(7, 14),
                    product=product,
                    status=AdStatus.ACTIVE
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
            shipping = random.uniform(5, 15)
            
            order = Order.objects.create(
                tenant=vendor,
                order_number=order_num,
                total=0,
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
                    'sales_total': random.uniform(500, 2000),
                    'conversion_rate': random.uniform(2, 8),
                    'visit_growth': random.uniform(0, 10)
                }
            )
            
            # Messages
            ContactMessage.objects.create(
                name=f"Customer {random.randint(1, 100)}",
                email=f"customer{random.randint(1, 100)}@example.com",
                message="I have a question about my recent order. Can you please help?",
            )

        # 11. OTP Codes
        self.stdout.write("Generating OTPs...")
        for i in range(5):
            OTPCode.objects.create(
                email=f"test_user_{i}@example.com",
                code_type=random.choice(CodeTypes.values)
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))

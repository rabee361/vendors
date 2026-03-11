import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from faker import Faker
from base.models import (
    Buyer, Vendor, StoreCategory, ProductCategory, Product, 
    Offer, SponsoredAd, Cart, CartItem, Favorite, Order, 
    OrderItem, ContactMessage, VendorStats, OTPCode
)
from utils.types import UserType, AdType, AdStatus, OrderStatus, CodeTypes
import os

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with fake data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Populating database...")

        # 1. Create Store Categories
        self.stdout.write("Generating Store Categories...")
        store_categories = []
        for _ in range(5):
            name = fake.unique.company()
            cat, created = StoreCategory.objects.get_or_create(
                name=name,
                defaults={'description': fake.text(max_nb_chars=200)}
            )
            store_categories.append(cat)

        # 2. Create Users (Buyers, Sellers, Admins)
        self.stdout.write("Generating Users...")
        all_users = []
        
        # Admin
        for _ in range(2):
            email = fake.unique.email()
            user = User.objects.create_user(
                username=email,
                email=email,
                password='password123',
                user_type=UserType.ADMIN
            )
            all_users.append(user)

        # 3. Create Vendors (Sellers)
        self.stdout.write("Generating Vendors...")
        vendors = []
        # Update path to use settings.STATICFILES_DIRS[0] which is BASE_DIR / "static"
        placeholder_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'placeholder.jfif')
        
        for _ in range(5):
            email = fake.unique.email()
            user = User.objects.create_user(
                username=email,
                email=email,
                password='password123',
                user_type=UserType.SELLER
            )
            all_users.append(user)
            
            vendor = Vendor.objects.create(
                user=user,
                store_name=fake.company(),
                category=random.choice(store_categories),
                rating=random.uniform(3.0, 5.0),
                address=fake.address(),
                phone=fake.phone_number()[:20],
                is_active=True
            )
            
            if os.path.exists(placeholder_path):
                with open(placeholder_path, 'rb') as f:
                    vendor.avatar.save('avatar.jfif', File(f), save=True)
            
            vendors.append(vendor)

        # 4. Create Buyers
        self.stdout.write("Generating Buyers...")
        buyers = []
        for _ in range(8):
            email = fake.unique.email()
            user = User.objects.create_user(
                username=email,
                email=email,
                password='password123',
                user_type=UserType.BUYER
            )
            all_users.append(user)
            
            buyer = Buyer.objects.create(
                user=user,
                address=fake.address()
            )
            buyers.append(buyer)

        # 5. Create Product Categories and Products
        self.stdout.write("Generating Products and Categories...")
        all_products = []
        for vendor in vendors:
            for _ in range(3):
                p_cat_name = fake.unique.word().capitalize() + " " + str(random.randint(1, 1000))
                p_cat = ProductCategory.objects.create(
                    tenant=vendor,
                    name=p_cat_name,
                    description=fake.sentence()
                )
                
                for _ in range(random.randint(5, 10)):
                    product = Product.objects.create(
                        tenant=vendor,
                        name=fake.catch_phrase(),
                        description=fake.text(),
                        price=random.uniform(10.0, 500.0),
                        stock=random.randint(0, 100),
                        category=p_cat,
                        rating=random.uniform(3.0, 5.0),
                        rating_count=random.randint(0, 100),
                        is_active=True
                    )
                    
                    if os.path.exists(placeholder_path):
                        with open(placeholder_path, 'rb') as f:
                            product.image.save('product.jfif', File(f), save=True)
                    
                    all_products.append(product)

        # 6. Create Deals
        self.stdout.write("Generating Deals...")
        for vendor in vendors:
            vendor_products = [p for p in all_products if p.tenant == vendor]
            if vendor_products:
                for _ in range(random.randint(1, 3)):
                    prod = random.choice(vendor_products)
                    Offer.objects.create(
                        tenant=vendor,
                        product=prod,
                        discount=random.randint(5, 50),
                        original_price=prod.price,
                        start_date=fake.date_this_year(),
                        end_date=fake.date_between(start_date='today', end_date='+30d'),
                        is_active=True
                    )

        # 7. Create Sponsored Ads
        self.stdout.write("Generating Ads...")
        if all_products:
            for _ in range(5):
                 SponsoredAd.objects.create(
                    ad_type=random.choice(AdType.values),
                    budget=random.uniform(50, 500),
                    days_count=random.randint(7, 30),
                    product=random.choice(all_products),
                    status=AdStatus.ACTIVE
                )

        # 8. Create Carts and Favorites
        self.stdout.write("Generating Favorites and Carts...")
        buyer_users = [b.user for b in buyers]
        for user in buyer_users:
            # Favorites
            if all_products:
                fav_prods = random.sample(all_products, k=min(len(all_products), random.randint(1, 5)))
                for p in fav_prods:
                    Favorite.objects.get_or_create(user=user, product=p)
            
            # Cart
            cart = Cart.objects.create(user=user)
            if all_products:
                cart_prods = random.sample(all_products, k=min(len(all_products), random.randint(1, 3)))
                for p in cart_prods:
                    CartItem.objects.create(cart=cart, product=p, quantity=random.randint(1, 5))

        # 9. Create Orders
        self.stdout.write("Generating Orders...")
        for _ in range(10):
            vendor = random.choice(vendors)
            order_num = f"ORD-{fake.unique.numerify('#####')}"
            shipping = random.uniform(5, 20)
            
            order = Order.objects.create(
                tenant=vendor,
                order_number=order_num,
                total=0, # To be calculated
                shipping_cost=shipping,
                status='preparing'
            )
            
            order_total = 0
            vendor_prods = [p for p in all_products if p.tenant == vendor]
            if vendor_prods:
                items_to_add = random.sample(vendor_prods, k=min(len(vendor_prods), random.randint(1, 3)))
                for p in items_to_add:
                    qty = random.randint(1, 3)
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
            VendorStats.objects.create(
                tenant=vendor,
                week_start=fake.date_this_month(),
                views=random.randint(100, 1000),
                sales_total=random.uniform(1000, 5000),
                conversion_rate=random.uniform(1, 10),
                visit_growth=random.uniform(-5, 15)
            )
            
            # Messages
            for _ in range(3):
                ContactMessage.objects.create(
                    tenant=vendor,
                    name=fake.name(),
                    email=fake.email(),
                    message=fake.paragraph(),
                    is_read=random.choice([True, False])
                )

        # 11. OTP Codes
        self.stdout.write("Generating OTPs...")
        for _ in range(10):
            OTPCode.objects.create(
                email=fake.email(),
                code_type=random.choice(CodeTypes.values)
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))

import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from base.models import Order, OrderItem, Product, StoreCategory, Vendor
from base.models import CustomUser as User



class APILoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer-1',
            email='buyer1@test.com',
            password='pass123',
            first_name='Buyer One',
        )

    def test_login_returns_token(self):
        response = self.client.post(
            reverse('api:login'),
            data=json.dumps({
                'email': 'buyer1@test.com',
                'password': 'pass123',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
        self.assertTrue(Token.objects.filter(user=self.user).exists())


class ProductListAPITests(TestCase):
    def setUp(self):
        category = StoreCategory.objects.create(name='Electronics')
        self.api_user = User.objects.create_user(username='buyer-products', email='buyer-products@test.com', password='pass123')
        self.token = Token.objects.create(user=self.api_user)
        vendor_user = User.objects.create_user(username='vendor-1', email='vendor1@test.com', password='pass123')
        vendor = Vendor.objects.create(user=vendor_user, store_name='Store One', category=category)
        Product.objects.create(name='Active Product', price=10, stock=5, tenant=vendor, image='active.jpg', is_active=True)
        Product.objects.create(name='Inactive Product', price=20, stock=2, tenant=vendor, image='inactive.jpg', is_active=False)

    def test_requires_token_for_product_list(self):
        response = self.client.get(reverse('api:product-list'))

        self.assertEqual(response.status_code, 401)

    def test_lists_active_products_across_vendors(self):
        response = self.client.get(
            reverse('api:product-list'),
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['name'], 'Active Product')


class OrderCreateAPITests(TestCase):
    def setUp(self):
        category = StoreCategory.objects.create(name='General')
        self.api_user = User.objects.create_user(username='buyer-orders', email='buyer-orders@test.com', password='pass123')
        self.token = Token.objects.create(user=self.api_user)
        vendor_user_1 = User.objects.create_user(username='vendor-2', email='vendor2@test.com', password='pass123')
        vendor_user_2 = User.objects.create_user(username='vendor-3', email='vendor3@test.com', password='pass123')
        self.vendor_one = Vendor.objects.create(user=vendor_user_1, store_name='Store A', category=category)
        self.vendor_two = Vendor.objects.create(user=vendor_user_2, store_name='Store B', category=category)
        self.product_one = Product.objects.create(
            name='Keyboard',
            price=Decimal('25.00'),
            stock=4,
            tenant=self.vendor_one,
            image='keyboard.jpg',
        )
        self.product_two = Product.objects.create(
            name='Mouse',
    def test_requires_token_for_order_creation(self):
        payload = {
            'email': 'buyer@test.com',
            'full_name': 'API Buyer',
            'phone': '+963912345678',
            'city': 'Damascus',
            'address': 'Main Street',
            'items': [
                {'product_id': self.product_one.id, 'quantity': 1},
            ],
        }

        response = self.client.post(
            reverse('api:order-create'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

            price=Decimal('15.00'),
            stock=6,
            tenant=self.vendor_two,
            image='mouse.jpg',
        )

    def test_creates_separate_orders_per_vendor(self):
        payload = {
            'email': 'buyer@test.com',
            'full_name': 'API Buyer',
            'phone': '+963912345678',
            'city': 'Damascus',
            'address': 'Main Street',
            'notes': 'Leave at the door',
            'items': [
                {'product_id': self.product_one.id, 'quantity': 2},
                {'product_id': self.product_two.id, 'quantity': 3},
            ],
        }

        response = self.client.post(
            reverse('api:order-create'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(OrderItem.objects.count(), 2)
        self.assertEqual(response.json()['orders_count'], 2)

        self.product_one.refresh_from_db()
        self.product_two.refresh_from_db()
        self.assertEqual(self.product_one.stock, 2)
        self.assertEqual(self.product_two.stock, 3)

    def test_rejects_order_when_stock_is_insufficient(self):
        payload = {
            'email': 'buyer@test.com',
            'full_name': 'API Buyer',
            'phone': '+963912345678',
            'city': 'Damascus',
            'address': 'Main Street',
            'items': [
                {'product_id': self.product_one.id, 'quantity': 10},
            ],
        }

        response = self.client.post(
            reverse('api:order-create'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
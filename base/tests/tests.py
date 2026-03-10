from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Buyer, Vendor, StoreCategory

User = get_user_model()

class AuthenticationTests(TestCase):
    def test_buyer_signup(self):
        response = self.client.post(reverse('buyer_signup'), {
            'full_name': 'Test Buyer',
            'email': 'buyer@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='buyer@test.com').exists())
        self.assertTrue(Buyer.objects.filter(user__email='buyer@test.com').exists())

    def test_vendor_signup(self):
        response = self.client.post(reverse('vendor_signup'), {
            'full_name': 'Test Vendor',
            'email': 'vendor@test.com',
            'address': 'Test Address',
            'password': 'password123',
            'confirm_password': 'password123',
            'store_name': 'Test Store',
            'store_category': 'Electronics',
            'phone': '+963912345678'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='vendor@test.com').exists())
        self.assertTrue(Vendor.objects.filter(user__email='vendor@test.com').exists())
        self.assertTrue(StoreCategory.objects.filter(name='Electronics').exists())

    def test_login_flow(self):
        User.objects.create_user(
            username='user@test.com', 
            email='user@test.com', 
            password='password123',
            user_type=User.BUYER
        )
        response = self.client.post(reverse('login'), {
            'email': 'user@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        # Should redirect to 'home' because it's a buyer
        self.assertEqual(response.url, reverse('home'))

    def test_phone_validation_fail(self):
        response = self.client.post(reverse('vendor_signup'), {
            'full_name': 'Test Vendor',
            'email': 'vendor2@test.com',
            'address': 'Test Address',
            'password': 'password123',
            'confirm_password': 'password123',
            'store_name': 'Test Store',
            'store_category': 'Electronics',
            'phone': '12345'  # Invalid phone
        })
        self.assertEqual(response.status_code, 200) # Form should re-render with errors
        self.assertFalse(User.objects.filter(email='vendor2@test.com').exists())

class CheckoutViewTests(TestCase):
    def setUp(self):
        self.category = StoreCategory.objects.create(name="Tech")
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(username="v", email="v@t.com", password="p"),
            store_name="S",
            category=self.category
        )
        self.p1 = Product.objects.create(name="P1", price=10, tenant=self.vendor, image="p1.jpg")
        self.user = User.objects.create_user(username="b", email="b@t.com", password="p", first_name="Test")
        self.client.login(email="b@t.com", password="p")

    def test_checkout_get_empty_cart(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)

    def test_checkout_get_with_items(self):
        self.client.post(reverse('add_to_cart', args=[self.p1.id]), {'quantity': 1})
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "P1")

    def test_checkout_post_creates_orders(self):
        from ..models import Order, OrderItem
        self.client.post(reverse('add_to_cart', args=[self.p1.id]), {'quantity': 1})
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Buyer',
            'phone': '0912345678',
            'city': 'Damascus',
            'address': 'Street 1'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

class AccountUpdateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="b2", email="b2@t.com", password="p", first_name="Old")
        self.client.login(email="b2@t.com", password="p")

    def test_account_update(self):
        response = self.client.post(reverse('account_update'), {
            'display_name': 'New Name',
            'phone': '123456'
        }, HTTP_REFERER=reverse('home'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New Name')
        self.assertEqual(self.user.phone, '123456')

class ButtonStateTests(TestCase):
    def setUp(self):
        self.category = StoreCategory.objects.create(name="Tech")
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(username="v3", email="v3@t.com", password="p"),
            store_name="S3",
            category=self.category
        )
        self.p1 = Product.objects.create(name="P1", price=10, tenant=self.vendor, image="p1.jpg")

    def test_cart_context_has_product_ids(self):
        self.client.post(reverse('add_to_cart', args=[self.p1.id]), {'quantity': 1})
        from ..cart import CartService
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.session = self.client.session
        request.user = self.client.session.get('_auth_user_id', None) # Simplified
        
        # Checking if the key exists in our modified context
        cart_service = CartService(request)
        self.assertIn('cart_product_ids', cart_service.get_context())
        self.assertIn(str(self.p1.id), cart_service.get_context()['cart_product_ids'])

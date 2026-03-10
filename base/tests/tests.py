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

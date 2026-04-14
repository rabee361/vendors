from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from utils.types import AdStatus, AdType, UserType

from ..forms import SponsoredAdForm
from ..models import Buyer, Vendor, StoreCategory, Product, Setting, SponsoredAd, SponsoredAdClick

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


class SponsoredAdFormTests(TestCase):
    def setUp(self):
        self.category = StoreCategory.objects.create(name='Ads Category')
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(username='vendor-ads', email='vendor-ads@test.com', password='p'),
            store_name='Ads Store',
            category=self.category,
        )
        self.product = Product.objects.create(
            name='Ad Product',
            price=20,
            tenant=self.vendor,
            image='ad-product.jpg',
        )

    def test_section_ads_require_budget_at_or_above_minimum(self):
        Setting.objects.create(name='minimum_ad_budget', value='25')

        form = SponsoredAdForm(
            data={
                'ad_type': AdType.SECTION,
                'product': self.product.id,
                'budget': 10,
                'status': AdStatus.ACTIVE,
                'end_date': (timezone.localdate() + timedelta(days=7)).isoformat(),
            },
            vendor=self.vendor,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('budget', form.errors)

    def test_badge_ads_use_fixed_budget_from_settings(self):
        Setting.objects.create(name='normal_ads_budget', value='40')

        form = SponsoredAdForm(
            data={
                'ad_type': AdType.BADGE,
                'product': self.product.id,
                'budget': 5,
                'status': AdStatus.ACTIVE,
                'end_date': (timezone.localdate() + timedelta(days=7)).isoformat(),
            },
            vendor=self.vendor,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['budget'], 40)

    def test_badge_ads_do_not_require_budget_submission(self):
        Setting.objects.create(name='normal_ads_budget', value='40')

        form = SponsoredAdForm(
            data={
                'ad_type': AdType.BADGE,
                'product': self.product.id,
                'status': AdStatus.ACTIVE,
                'end_date': (timezone.localdate() + timedelta(days=7)).isoformat(),
            },
            vendor=self.vendor,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['budget'], 40)

    def test_missing_settings_fall_back_to_defaults(self):
        form = SponsoredAdForm(vendor=self.vendor)

        self.assertEqual(form.minimum_ad_budget, 10)
        self.assertEqual(form.normal_ads_budget, 10)
        self.assertEqual(form.ad_click_cost_display, 1)


class SponsoredAdClickRedirectTests(TestCase):
    def setUp(self):
        self.category = StoreCategory.objects.create(name='Ads Redirect Category')
        self.vendor_user = User.objects.create_user(
            username='redirect-vendor',
            email='redirect-vendor@test.com',
            password='p',
        )
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            store_name='Redirect Ads Store',
            category=self.category,
        )
        self.product = Product.objects.create(
            name='Redirect Ad Product',
            price=20,
            tenant=self.vendor,
            image='redirect-product.jpg',
        )

    @patch('base.sponsored_ads.send_ad_budget_exhausted_email')
    def test_redirect_inactivates_ad_when_budget_click_limit_is_reached(self, send_email_mock):
        Setting.objects.create(name='ad_click_cost', value='2')
        ad = SponsoredAd.objects.create(
            tenant=self.vendor,
            ad_type=AdType.SECTION,
            product=self.product,
            status=AdStatus.ACTIVE,
            end_date=timezone.localdate() + timedelta(days=7),
            budget=4,
        )

        first_client = Client()
        second_client = Client()

        first_response = first_client.get(reverse('sponsored_ad_click', args=[ad.id]), {'source': 'home'})
        self.assertEqual(first_response.status_code, 302)

        ad.refresh_from_db()
        self.assertEqual(ad.clicks, 1)
        self.assertEqual(ad.status, AdStatus.ACTIVE)
        send_email_mock.assert_not_called()

        second_response = second_client.get(reverse('sponsored_ad_click', args=[ad.id]), {'source': 'ads'})
        self.assertEqual(second_response.status_code, 302)

        ad.refresh_from_db()
        self.assertEqual(ad.clicks, 2)
        self.assertEqual(ad.status, AdStatus.INACTIVE)
        self.assertEqual(SponsoredAdClick.objects.filter(ad=ad).count(), 2)
        send_email_mock.assert_called_once()

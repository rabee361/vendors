from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Product, Vendor, StoreCategory, Favorite
from ..favorite import FavoriteService

User = get_user_model()

class FavoriteServiceTests(TestCase):
    def setUp(self):
        self.category = StoreCategory.objects.create(name="Tech")
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(username="v", email="v@t.com", password="p"),
            store_name="S",
            category=self.category
        )
        self.p1 = Product.objects.create(name="P1", price=10, tenant=self.vendor, image="p1.jpg")
        self.p2 = Product.objects.create(name="P2", price=20, tenant=self.vendor, image="p2.jpg")
        self.client = Client()

    def test_anonymous_favorites(self):
        # Initial empty
        self.client.get(reverse('home')) # Init session
        response = self.client.post(reverse('toggle_favorite', args=[self.p1.id]))
        self.assertIn('favorites', self.client.session)
        self.assertIn(str(self.p1.id), self.client.session['favorites'])
        
        # Toggle off
        self.client.post(reverse('toggle_favorite', args=[self.p1.id]))
        self.assertNotIn(str(self.p1.id), self.client.session['favorites'])

    def test_sync_to_db(self):
        # Add as anonymous
        self.client.post(reverse('toggle_favorite', args=[self.p1.id]))
        
        # Create user and log in
        user = User.objects.create_user(username="b", email="b@t.com", password="p")
        self.client.post(reverse('login'), {'email': 'b@t.com', 'password': 'p'})
        
        # Check DB
        self.assertTrue(Favorite.objects.filter(user=user, product=self.p1).exists())
        # Check session cleared
        self.assertEqual(len(self.client.session.get('favorites', [])), 0)

    def test_remove_view(self):
        self.client.post(reverse('toggle_favorite', args=[self.p1.id]))
        response = self.client.post(reverse('remove_favorite', args=[self.p1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(self.p1.id), self.client.session.get('favorites', []))

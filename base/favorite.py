from django.conf import settings
from .models import Favorite, Product

class FavoriteService:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        favorites = self.session.get('favorites')
        if not favorites:
            favorites = self.session['favorites'] = []
        self.favorites = favorites 

    def add(self, product_id):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            Favorite.objects.get_or_create(user=self.request.user, product_id=product_id)
        else:
            if product_id not in self.favorites:
                self.favorites.append(product_id)
                self.save()

    def remove(self, product_id):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            Favorite.objects.filter(user=self.request.user, product_id=product_id).delete()
        else:
            if product_id in self.favorites:
                self.favorites.remove(product_id)
                self.save()

    def toggle(self, product_id):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            favorite, created = Favorite.objects.get_or_create(user=self.request.user, product_id=product_id)
            if not created:
                favorite.delete()
                return "removed"
            return "added"
        else:
            if product_id in self.favorites:
                self.favorites.remove(product_id)
                self.save()
                return "removed"
            else:
                self.favorites.append(product_id)
                self.save()
                return "added"

    def contains(self, product_id):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            return Favorite.objects.filter(user=self.request.user, product_id=product_id).exists()
        return product_id in self.favorites

    def save(self):
        self.session['favorites'] = self.favorites
        self.session.modified = True

    def get_context(self):
        favorite_items = []
        favorites_count = 0
        
        if self.request.user.is_authenticated:
            items = Favorite.objects.filter(user=self.request.user).select_related('product', 'product__category')
            # Extract just the products for the template
            favorite_items = [fav.product for fav in items]
            favorites_count = len(favorite_items)
        else:
            products = Product.objects.filter(id__in=self.favorites).select_related('category')
            favorite_items = list(products)
            favorites_count = len(favorite_items)

        return {
            'favorite_items': favorite_items,
            'favorites_count': favorites_count,
            'favorite_product_ids': [str(p.id) for p in favorite_items]
        }

    def sync_to_db(self, user):
        if self.favorites:
            for product_id in self.favorites:
                Favorite.objects.get_or_create(user=user, product_id=product_id)
            
            self.session['favorites'] = []
            self.session.modified = True

    def clear(self):
        self.session['favorites'] = []
        self.session.modified = True

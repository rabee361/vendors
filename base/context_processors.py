from .cart import CartService
from .favorite import FavoriteService

def cart_context(request):
    cart = CartService(request)
    return cart.get_context()

def favorites_context(request):
    fav = FavoriteService(request)
    return fav.get_context()

from .cart import CartService
from .favorite import FavoriteService
from utils.types import UserType


def cart_context(request):
    cart = CartService(request)
    return cart.get_context()

def favorites_context(request):
    fav = FavoriteService(request)
    return fav.get_context()

def vendor_context(request):
    if request.user.is_authenticated and request.user.user_type == UserType.SELLER:
        return {'vendor_id': request.user.vendor_profile.id}
    return {'vendor_id': 0}

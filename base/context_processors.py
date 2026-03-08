from .models import Cart, Favorite

def cart_context(request):
    cart_items = []
    cart_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        cart_count = items.count()
        cart_items = items
    else:
        session_key = request.session.session_key
        if session_key:
            cart, created = Cart.objects.get_or_create(session_key=session_key)
            items = cart.items.all()
            cart_count = items.count()
            cart_items = items
            
    return {
        'cart_items': cart_items,
        'cart_count': cart_count,
    }

def favorites_context(request):
    favorites_count = 0
    favorite_items = []
    if request.user.is_authenticated:
        items = request.user.favorites.all()
        favorites_count = items.count()
        favorite_items = items
        
    return {
        'favorites_count': favorites_count,
        'favorite_items': favorite_items,
    }

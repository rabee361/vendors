from django.conf import settings
from .models import Cart, CartItem, Product

class CartService:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product_id, quantity=1, override_quantity=False):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            cart_obj, _ = Cart.objects.get_or_create(user=self.request.user)
            item, created = CartItem.objects.get_or_create(cart=cart_obj, product_id=product_id)
            if override_quantity:
                item.quantity = quantity
            else:
                if not created:
                    item.quantity += quantity
                else:
                    item.quantity = quantity
            item.save()
        else:
            if product_id in self.cart:
                if override_quantity:
                    self.cart[product_id] = quantity
                else:
                    self.cart[product_id] += quantity
            else:
                self.cart[product_id] = quantity
            self.save()

    def remove(self, product_id):
        product_id = str(product_id)
        if self.request.user.is_authenticated:
            CartItem.objects.filter(cart__user=self.request.user, product_id=product_id).delete()
        else:
            if product_id in self.cart:
                del self.cart[product_id]
                self.save()

    def update(self, product_id, quantity):
        self.add(product_id, quantity, override_quantity=True)

    def save(self):
        self.session['cart'] = self.cart
        self.session.modified = True

    def get_context(self):
        grouped_items = {}
        cart_count = 0
        total_price = 0
        
        if self.request.user.is_authenticated:
            cart_obj, _ = Cart.objects.get_or_create(user=self.request.user)
            if not cart_obj.session_key and self.request.session.session_key:
                cart_obj.session_key = self.request.session.session_key
                cart_obj.save()
            items = cart_obj.items.select_related('product', 'product__tenant').prefetch_related('product__offers').all()
            for item in items:
                vendor = item.product.tenant
                if vendor not in grouped_items:
                    grouped_items[vendor] = {
                        'items': [],
                        'subtotal': 0
                    }
                current_price = item.product.current_price
                item_total = item.quantity * current_price
                grouped_items[vendor]['items'].append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': current_price,
                    'total': item_total,
                    'id': item.id
                })
                grouped_items[vendor]['subtotal'] += item_total
                cart_count += item.quantity
                total_price += item_total
                
        else:
            product_ids = self.cart.keys()
            products = Product.objects.select_related('tenant').prefetch_related('offers').filter(id__in=product_ids)
            for product in products:
                quantity = self.cart[str(product.id)]
                vendor = product.tenant
                if vendor not in grouped_items:
                    grouped_items[vendor] = {
                        'items': [],
                        'subtotal': 0
                    }
                current_price = product.current_price
                item_total = quantity * current_price
                grouped_items[vendor]['items'].append({
                    'product': product,
                    'quantity': quantity,
                    'price': current_price,
                    'total': item_total,
                    'id': f"session_{product.id}"
                })
                grouped_items[vendor]['subtotal'] += item_total
                cart_count += quantity
                total_price += item_total

        # Suggested products: same vendor(s) as cart items, or random if cart empty
        if self.request.user.is_authenticated:
            cart_product_ids_list = [str(pid) for pid in CartItem.objects.filter(cart__user=self.request.user).values_list('product_id', flat=True)]
        else:
            cart_product_ids_list = list(self.cart.keys())
        vendor_ids = [v.id for v in grouped_items.keys()]

        if vendor_ids:
            suggested = Product.objects.filter(
                tenant_id__in=vendor_ids, is_active=True
            ).exclude(id__in=cart_product_ids_list).order_by('?')[:2]
        else:
            suggested = Product.objects.filter(is_active=True).order_by('?')[:2]

        return {
            'grouped_items': dict(grouped_items),
            'cart_count': cart_count,
            'cart_total': total_price,
            'cart_product_ids': cart_product_ids_list,
            'suggested_products': suggested
        }

    def get_items(self):
        return self.get_context()['grouped_items']

    def clear_by_vendor(self, vendor_id):
        if self.request.user.is_authenticated:
            CartItem.objects.filter(
                cart__user=self.request.user, 
                product__tenant_id=vendor_id
            ).delete()
        else:
            product_ids_to_remove = []
            # Use Product.objects to find which products in session belong to this vendor
            p_ids = [int(pid) for pid in self.cart.keys() if pid.isdigit()]
            matching_products = Product.objects.filter(id__in=p_ids, tenant_id=vendor_id)
            for p in matching_products:
                product_ids_to_remove.append(str(p.id))
            
            for pid in product_ids_to_remove:
                if pid in self.cart:
                    del self.cart[pid]
            self.save()

    def sync_to_db(self, user):
        if self.cart:
            cart_obj, created = Cart.objects.get_or_create(user=user)
            if self.request.session.session_key:
                cart_obj.session_key = self.request.session.session_key
                cart_obj.save()
                
            for product_id, quantity in self.cart.items():
                item, item_created = CartItem.objects.get_or_create(cart=cart_obj, product_id=product_id)
                # Overriding the DB quantity with session quantity
                item.quantity = quantity
                item.save()
            
            # Clear session cart after sync
            self.session['cart'] = {}
            self.session.modified = True

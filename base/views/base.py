from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import FormView, View
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef

from django.contrib.auth import login, logout, authenticate, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from ..forms import *
from utils.types import UserType, CodeTypes
from utils.email import send_otp_email
from utils.mixins import UserAlreadyLoggedInMixin
from urllib.parse import quote
from ..cart import CartService
from ..favorite import FavoriteService
from django.db.models import Q, Avg
from ..models import *
import uuid
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.utils import timezone

User = get_user_model()


class HomeView(View):
    def get(self, request):

        if request.htmx:
            template_name = 'base/partials/products_partial.html'
        else:
            template_name = 'base/index.html'

        message_form = MessageForm()

        orders_count = Order.objects.count()
        vendor_count = Vendor.objects.filter(user__is_active=True).count()
        product_count = Product.objects.filter(is_active=True).count()
        category_count = ProductCategory.objects.count()

        query = request.GET.get('q', '')
        category_name = request.GET.get('category', '')
        min_price = request.GET.get('minPrice', '0')
        max_price = request.GET.get('maxPrice','99999')
        rating = request.GET.get('rating','')

        products = Product.objects.select_related('tenant', 'category', 'tenant__category').filter(is_active=True).annotate(avg_rating=Avg('ratings__rating'))

        if query:
            products = products.filter(name__icontains=query)
        if category_name:
            products = products.filter(category__name__icontains=category_name)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if rating:
            try:
                products = products.filter(avg_rating__gte=float(rating))
            except (TypeError, ValueError):
                pass

        products = products.annotate(
            is_ad_badge=Exists(
                SponsoredAd.objects.filter(
                    product=OuterRef('pk'), 
                    ad_type=AdType.BADGE, 
                    status=AdStatus.ACTIVE,
                    start_date__lte=timezone.now(),
                    end_date__gte=timezone.now()
                )
            )
        )

        vendors = Vendor.objects.select_related('category').filter(user__is_active=True)[:3]
        offers = Offer.objects.filter(is_active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())[:3]
        ads = SponsoredAd.objects.filter(Q(ad_type=AdType.SECTION) & Q(start_date__lte=timezone.now()) & Q(end_date__gte=timezone.now()))[:3]
        categories = ProductCategory.objects.all()[:4]
        context = { 
            'vendors': vendors,
            'categories': categories,
            'products': products[:6],
            'ads': ads,
            'offers': offers,
            'query': query,
            'category_name': category_name,
            'min_price': min_price,
            'max_price': max_price,
            'rating': rating,
            'orders_count': orders_count,
            'vendor_count': vendor_count,
            'product_count': product_count,
            'category_count': category_count,
            'message_form': message_form,
        }
        return render(request, template_name, context)
    
    def post(self, request):
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            message_form.save()
            if request.htmx:
                response = render(request, 'base/partials/contact_form.html', {'message_form': MessageForm()})
                response['X-Toast-Message'] = quote("تم إرسال رسالتك بنجاح! شكراً لتواصلك معنا.")
                response['X-Toast-Title'] = quote("تم الإرسال")
                response['X-Toast-Type'] = "success"
                return response
            return redirect('home')
        
        if request.htmx:
            return render(request, 'base/partials/contact_form.html', {'message_form': message_form})
        return render(request, 'base/index.html', {'message_form': message_form})


class BuyerSignupView(UserAlreadyLoggedInMixin, FormView):
    template_name = 'auth/buyer-signup.html'
    form_class = BuyerSignupForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['full_name'],
            user_type=UserType.BUYER
        )
        Buyer.objects.create(user=user)
        login(self.request, user)
        CartService(self.request).sync_to_db(user)
        FavoriteService(self.request).sync_to_db(user)
        return super().form_valid(form)

class LoginView(UserAlreadyLoggedInMixin, View):
    template_name = 'auth/login.html'

    def get(self, request):
        buyer_form = BuyerLoginForm()
        seller_form = SellerLoginForm()
        return render(request, self.template_name, {
            'buyer_form': buyer_form,
            'seller_form': seller_form
        })

    def post(self, request):
        login_type = request.POST.get('login_type')
        buyer_form = BuyerLoginForm()
        seller_form = SellerLoginForm()

        if login_type == 'buyer':
            form = BuyerLoginForm(request.POST)
            buyer_form = form
            if form.is_valid():
                user = form.cleaned_data['user']
                login(request, user)
                CartService(request).sync_to_db(user)
                FavoriteService(request).sync_to_db(user)
                return redirect('home')
        elif login_type == 'seller':
            form = SellerLoginForm(request.POST)
            seller_form = form
            if form.is_valid():
                user = form.cleaned_data['user']
                login(request, user)
                CartService(request).sync_to_db(user)
                FavoriteService(request).sync_to_db(user)
                return redirect('vendor_dashboard')
        
        return render(request, self.template_name, {
            'buyer_form': buyer_form,
            'seller_form': seller_form
        })

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')

class OtpCodeView(FormView):
    template_name = 'auth/otp.html'
    form_class = OTPForm
    success_url = reverse_lazy('verify_otp')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.get(email=email)
        
        # Create OTP for Password Reset
        otp_code = user.create_otp(code_type=CodeTypes.RESET_PASSWORD)
        self.request.session['signup_email'] = email
        
        # Send OTP Email
        send_otp_email(otp_code, email)
        
        return super().form_valid(form)


class VerifyOtpView(View):
    template_name = 'auth/verify.html'
    
    def get(self, request):
        form = VerifyOTPForm()
        email = request.session.get('signup_email')
        return render(request, self.template_name, {
            'form': form, 
            'email': email
        })

    def post(self, request):
        form = VerifyOTPForm(request.POST)
        email = request.session.get('signup_email')
        
        if form.is_valid():
            code = form.cleaned_data['code']
            otp = OTPCode.objects.filter(email=email, code=code, is_used=False).first()
            
            if otp and not otp.is_expired:
                otp.is_used = True
                otp.save()
                
                if email:
                    try:
                        user = User.objects.get(email=email)
                        if user:
                            user.is_verified = True
                            user.save()
                            authenticate(request, username=user.email, password=None)
                            login(request, user)
                            if user.user_type == UserType.SELLER:
                                return redirect('vendor_dashboard')
                    except User.DoesNotExist:
                        pass
                return redirect('home')
            
            form.add_error('code', "رمز التحقق غير صحيح أو منتهي الصلاحية.")
        
        return render(request, self.template_name, {
            'form': form, 
            'email': email
        })


class ChangePasswordView(LoginRequiredMixin, View):
    def get(self, request):
        form = ChangePasswordForm(user=request.user)
        return render(request, "auth/change_password.html", {'form':form})

    def post(self, request):
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to stay logged in
            return redirect('home')
        return render(request, "auth/change_password.html", {'form':form})

# class ResetPasswordView(View):
#     def get(self, request):
#         form = ResetPasswordForm()
#         return render(request, "auth/reset_password.html", {'form':form})

#     def post(self, request):
#         form = ResetPasswordForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('login')
#         return render(request, "auth/reset_password.html", {'form':form})

class VendorsView(View):
    def get(self, request):
        vendors = Vendor.objects.select_related('category').filter(user__is_active=True)
        return render(request, "base/vendors.html", {'vendors': vendors})

class CategoriesView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        categories = ProductCategory.objects.all()
        if query:
            categories = categories.filter(name__icontains=query)
        return render(request, "base/categories.html", {'categories': categories, 'query': query})

class OfferListView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        offers = Offer.objects.all()
        if query:
            offers = offers.filter(product__name__icontains=query)
        return render(request, "base/offers.html", {'offers': offers, 'query': query})

class AdListView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        ads = SponsoredAd.objects.all()
        if query:
            ads = ads.filter(product__name__icontains=query)
        return render(request, "base/ads.html", {'ads': ads, 'query': query})


class ProductListView(View):
    paginate_by = 12

    def get(self, request):
        if self.request.htmx:
            template_name = 'base/partials/products_partial.html'
        else:
            template_name = 'base/products.html'

        query = request.GET.get('q', '')
        category_name = request.GET.get('category', '')
        min_price = request.GET.get('minPrice','0')
        max_price = request.GET.get('maxPrice','999999')
        rating = request.GET.get('rating','')

        products_list = Product.objects.select_related('tenant', 'category', 'tenant__category').filter(is_active=True).annotate(avg_rating=Avg('ratings__rating'))

        if query:
            products_list = products_list.filter(name__icontains=query)
        if category_name:
            products_list = products_list.filter(category__name__icontains=category_name)
        if min_price:
            products_list = products_list.filter(price__gte=min_price)
        if max_price:
            products_list = products_list.filter(price__lte=max_price)
        if rating:
            try:
                products_list = products_list.filter(avg_rating__gte=float(rating))
            except (TypeError, ValueError):
                pass
            
        products_list = products_list.annotate(
            is_ad_badge=Exists(
                SponsoredAd.objects.filter(
                    product=OuterRef('pk'), 
                    ad_type=AdType.BADGE, 
                    status=AdStatus.ACTIVE,
                    start_date__lte=timezone.now(),
                    end_date__gte=timezone.now()
                )
            )
        )

        paginator = Paginator(products_list, self.paginate_by)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)

        categories = ProductCategory.objects.all()
        
        context = {
            'products': products,
            'categories': categories,
            'query': query,
            'category_name': category_name,
            'min_price': min_price,
            'max_price': max_price,
            'rating': rating,
        }

            
        return render(request, template_name, context)


class ProductDetailView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product.objects.select_related('tenant', 'category', 'tenant__category'), id=product_id)
        
        # Get 6 newest active products from the same store, excluding this product
        store_products = Product.objects.filter(
            tenant=product.tenant, 
            is_active=True
        ).exclude(id=product.id).order_by('-created_at')[:6]

        # Get the user's rating if they are logged in
        user_rating = None
        if request.user.is_authenticated:
            user_rating_obj = ProductRating.objects.filter(user=request.user, product=product).first()
            if user_rating_obj:
                user_rating = user_rating_obj.rating

        cart_product_ids = []
        if request.user.is_authenticated:
            cart = CartService(request)
            cart_items = cart.get_items()
            cart_product_ids = [str(item.id) for item in getattr(cart_items, 'all', lambda: cart_items)()]

        context = {
            'product': product,
            'store_products': store_products,
            'user_rating': user_rating,
            'cart_product_ids': cart_product_ids
        }
        return render(request, 'base/product.html', context)

class RateProductView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        rating_val = request.POST.get('rating')
        
        try:
            rating_val = float(rating_val)
            if not (1.0 <= rating_val <= 5.0):
                raise ValueError("Rating out of bounds.")
        except (TypeError, ValueError):
            return HttpResponse("Invalid rating value.", status=400)

        # Create or update the rating
        ProductRating.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating_val}
        )

        context = {
            'product': product,
            'user_rating': rating_val
        }
        
        response = render(request, 'base/partials/rating_partial.html', context)
        response['X-Toast-Message'] = quote("تم حفظ التقييم بنجاح")
        response['X-Toast-Type'] = "success"
        response['X-Toast-Title'] = quote("تقييم المنتج")
        return response


class AddToCartView(View):
    def post(self, request, product_id):
        quantity = int(request.POST.get('quantity', 1))
        cart = CartService(request)
        cart.add(product_id, quantity)
        response = render(request, 'components/cart.html', cart.get_context())
        product = Product.objects.get(id=product_id)
        response['X-Toast-Message'] = quote(f"تمت إضافة {product.name} إلى السلة")
        response['X-Toast-Title'] = quote("تمت الإضافة")
        response['X-Toast-Type'] = "success"
        return response


class RemoveFromCartView(View):
    def post(self, request, product_id):
        cart = CartService(request)
        cart.remove(product_id)
        response = render(request, 'components/cart.html', cart.get_context())
        response['X-Toast-Message'] = quote("تمت إزالة المنتج من السلة")
        response['X-Toast-Title'] = quote("تمت الإزالة")
        response['X-Toast-Type'] = "info"
        return response


class UpdateCartView(View):
    def post(self, request, product_id):
        quantity = int(request.POST.get('quantity', 1))
        cart = CartService(request)
        if quantity > 0:
            cart.update(product_id, quantity)
        else:
            cart.remove(product_id)
        return render(request, 'components/cart.html', cart.get_context())


class CartHTMXView(View):
    def get(self, request):
        cart = CartService(request)
        return render(request, 'components/cart.html', cart.get_context())


class ToggleFavoriteView(View):
    def post(self, request, product_id):
        fav = FavoriteService(request)
        action = fav.toggle(product_id)
        
        product = Product.objects.get(id=product_id)
        if action == "added":
            msg = f"تمت إضافة {product.name} إلى المفضلة"
            type = "success"
        else:
            msg = f"تمت إزالة {product.name} من المفضلة"
            type = "info"
            
        response = render(request, 'components/favorites.html', fav.get_context())
        response['X-Toast-Message'] = quote(msg)
        response['X-Toast-Title'] = quote("المفضلة")
        response['X-Toast-Type'] = type
        return response


class RemoveFavoriteView(View):
    def post(self, request, product_id):
        fav = FavoriteService(request)
        fav.remove(product_id)
        
        response = render(request, 'components/favorites.html', fav.get_context())
        response['X-Toast-Message'] = quote("تمت إزالة المنتج من المفضلة")
        response['X-Toast-Title'] = quote("تمت الإزالة")
        response['X-Toast-Type'] = "info"
        return response


class AccountUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        form = AccountUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['display_name']
            user.phone = form.cleaned_data['phone']
            if form.cleaned_data['avatar']:
                user.avatar = form.cleaned_data['avatar']
            user.save()
        return redirect(request.META.get('HTTP_REFERER', 'home'))



class CheckoutView(LoginRequiredMixin, View):
    def get(self, request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        cart = CartService(request)
        context = cart.get_context()
        
        if vendor not in context['grouped_items']:
            return redirect('home')
        
        # Clear any previously applied coupons when entering checkout fresh
        request.session.pop('applied_coupons', None)
            
        vendor_data = context['grouped_items'][vendor]
        context['vendor'] = vendor
        context['items'] = vendor_data['items']
        context['total'] = vendor_data['subtotal']
        
        form = CheckoutForm(initial={
            'full_name': request.user.first_name,
            'phone': request.user.phone,
            'email': request.user.email
        })
        context['form'] = form
        return render(request, 'base/checkout.html', context)

    def post(self, request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        cart_service = CartService(request)
        cart_data = cart_service.get_context()
        form = CheckoutForm(request.POST)
        
        if form.is_valid() and vendor in cart_data['grouped_items']:
            data = cart_data['grouped_items'][vendor]
            subtotal = data['subtotal']
            
            # Calculate total discount from session coupons (value is a percentage)
            applied_codes = request.session.get('applied_coupons', [])
            total_percent = Decimal(0)
            
            for code in applied_codes:
                try:
                    c = Coupon.objects.get(
                        tenant=vendor,
                        code=code,
                        is_used=False,
                    )
                    if c.recipient_email and c.recipient_email != request.user.email:
                        continue
                    total_percent += c.value
                    c.is_used = True
                    c.save()
                except Coupon.DoesNotExist:
                    pass
            
            total_percent = min(total_percent, Decimal(100))
            total_discount = subtotal * total_percent / Decimal(100)
            final_total = subtotal - total_discount
            
            order = Order.objects.create(
                tenant=vendor,
                order_number=str(uuid.uuid4()).split('-')[0].upper(),
                total=subtotal,
                discount_amount=total_discount,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                city=form.cleaned_data['city'],
                address=form.cleaned_data['address'],
                notes=form.cleaned_data['notes'],
                status='preparing'
            )
            
            for item in data['items']:
                OrderItem.objects.create(
                    tenant=vendor,
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price_at_order=item['price']
                )
            
            # Clear session coupons and cart
            request.session.pop('applied_coupons', None)
            cart_service.clear_by_vendor(vendor_id)
            
            return redirect('checkout_success')
            
        if vendor not in cart_data['grouped_items']:
            return redirect('home')

        context = cart_service.get_context()
        vendor_data = context['grouped_items'][vendor]
        context['vendor'] = vendor
        context['items'] = vendor_data['items']
        context['total'] = vendor_data['subtotal']
        context['form'] = form
        return render(request, 'base/checkout.html', context)

class ValidateCouponHTMXView(View):
    def post(self, request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        coupon_code = request.POST.get('coupon_code', '').strip()

        cart_service = CartService(request)
        context = cart_service.get_context()
        if vendor not in context['grouped_items']:
            return render(request, 'base/partials/coupon_result.html', {'error': 'خطأ في السلة'})

        original_total = context['grouped_items'][vendor]['subtotal']
        applied_codes = request.session.get('applied_coupons', [])

        # Check if already applied
        if coupon_code in applied_codes:
            return render(request, 'base/partials/coupon_result.html', {'error': 'تم تطبيق هذا الكود مسبقاً'})

        coupon = Coupon.objects.filter(tenant=vendor, code=coupon_code).first()

        if not coupon:
            return render(request, 'base/partials/coupon_result.html', {'error': 'الكود غير صحيح'})

        if coupon.is_used:
            return render(request, 'base/partials/coupon_result.html', {'error': 'الكود مستخدم مسبقاً'})

        if not coupon.is_valid:
            return render(request, 'base/partials/coupon_result.html', {'error': 'الكود منتهي الصلاحية'})

        if coupon.recipient_email and coupon.recipient_email != request.user.email:
            return render(request, 'base/partials/coupon_result.html', {'error': 'هذا الكود مخصص لحساب آخر'})

        # Add to session (don't mark is_used yet)
        applied_codes.append(coupon_code)
        request.session['applied_coupons'] = applied_codes
        request.session.modified = True

        # Calculate accumulated discount (value is a percentage)
        total_percent = Decimal(0)
        applied_coupons_data = []
        for code in applied_codes:
            try:
                c = Coupon.objects.get(tenant=vendor, code=code, is_used=False)
                if c.recipient_email and c.recipient_email != request.user.email:
                    continue
                total_percent += c.value
                applied_coupons_data.append({
                    'code': c.code,
                    'percent': c.value,
                    'amount': original_total * c.value / Decimal(100),
                })
            except Coupon.DoesNotExist:
                pass

        total_percent = min(total_percent, Decimal(100))
        total_discount = original_total * total_percent / Decimal(100)
        new_total = original_total - total_discount

        return render(request, 'base/partials/coupon_result.html', {
            'applied_coupons': applied_coupons_data,
            'original_total': original_total,
            'total_discount': total_discount,
            'total_percent': total_percent,
            'new_total': new_total,
            'vendor_id': vendor_id,
        })


class RemoveCouponHTMXView(View):
    def post(self, request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        code_to_remove = request.POST.get('remove_code', '').strip()

        applied_codes = request.session.get('applied_coupons', [])
        if code_to_remove in applied_codes:
            applied_codes.remove(code_to_remove)
            request.session['applied_coupons'] = applied_codes
            request.session.modified = True

        cart_service = CartService(request)
        context = cart_service.get_context()
        if vendor not in context['grouped_items']:
            return render(request, 'base/partials/coupon_result.html', {'error': 'خطأ في السلة'})

        original_total = context['grouped_items'][vendor]['subtotal']

        if not applied_codes:
            # No coupons left, return empty state to reset totals
            return render(request, 'base/partials/coupon_result.html', {
                'cleared': True,
                'original_total': original_total,
            })

        total_percent = Decimal(0)
        applied_coupons_data = []
        for code in applied_codes:
            try:
                c = Coupon.objects.get(tenant=vendor, code=code, is_used=False)
                if c.recipient_email and c.recipient_email != request.user.email:
                    continue
                total_percent += c.value
                applied_coupons_data.append({
                    'code': c.code,
                    'percent': c.value,
                    'amount': original_total * c.value / Decimal(100),
                })
            except Coupon.DoesNotExist:
                pass

        total_percent = min(total_percent, Decimal(100))
        total_discount = original_total * total_percent / Decimal(100)
        new_total = original_total - total_discount

        return render(request, 'base/partials/coupon_result.html', {
            'applied_coupons': applied_coupons_data,
            'original_total': original_total,
            'total_discount': total_discount,
            'total_percent': total_percent,
            'new_total': new_total,
            'vendor_id': vendor_id,
        })

class CheckoutSuccess(View):
    def get(self, request):
        return render(request, 'components/checkout_success.html')

class handler404(View):
    def get(self, request):
        return render(request, 'components/404.html')

class handler500(View):
    def get(self, request):
        return render(request, 'components/500.html')


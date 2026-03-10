from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from ..forms import BuyerSignupForm, VendorSignupForm, BuyerLoginForm, SellerLoginForm, OTPForm, VerifyOTPForm
from ..models import Vendor, Product, ProductCategory, StoreCategory, Buyer, OTPCode, Favorite
from utils.types import UserType, CodeTypes
from utils.email import send_otp_email
from urllib.parse import quote
from ..cart import CartService
from ..favorite import FavoriteService
from ..forms import AccountUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()

class HomeView(View):
    def get(self, request):
        vendors = Vendor.objects.select_related('category').filter(is_active=True)[:4]
        categories = ProductCategory.objects.all()[:4]
        products = Product.objects.select_related('tenant', 'category', 'tenant__category').filter(is_active=True)[:6]
        return render(request, 'base/index.html', {'vendors': vendors, 'categories': categories, 'products': products})


class BuyerSignupView(FormView):
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
        messages.success(self.request, "تم إنشاء الحساب بنجاح!")
        return super().form_valid(form)


class VendorSignupView(FormView):
    template_name = 'auth/seller-signup.html'
    form_class = VendorSignupForm
    success_url = reverse_lazy('vendor_dashboard')

    def form_valid(self, form):
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['full_name'],
            user_type=UserType.SELLER
        )
        
        # Create OTP for Seller Signup
        otp_code = user.create_otp(code_type=CodeTypes.SIGNUP)
        self.request.session['signup_email'] = user.email
        
        # Send OTP Email
        send_otp_email(otp_code, user.email)
        messages.info(self.request, "تم إرسال رمز التحقق إلى بريدك الإلكتروني.")
        return redirect('verify_otp')


class LoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        buyer_form = BuyerLoginForm()
        seller_form = SellerLoginForm()
        return render(request, self.template_name, {
            'buyer_form': buyer_form,
            'seller_form': seller_form
        })

    def post(self, request):
        # Determine which form was submitted based on the button name or a hidden field
        if 'email' in request.POST and 'password' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user:
                login(request, user)
                CartService(request).sync_to_db(user)
                FavoriteService(request).sync_to_db(user)
                if user.is_seller:
                    return redirect('vendor_dashboard')
                return redirect('home')
            else:
                messages.error(request, "خطأ في البريد الإلكتروني أو كلمة المرور.")
        
        return self.get(request)


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
        # send_otp_email(otp_code, email)
        messages.success(self.request, "تم إرسال رمز التحقق إلى بريدك الإلكتروني.")
        
        return super().form_valid(form)


class VerifyOtpView(FormView):
    template_name = 'auth/verify.html'
    form_class = VerifyOTPForm
    
    def get_success_url(self):
        return reverse('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.session.get('signup_email')
        return context

    def form_valid(self, form):
        email = self.request.session.get('signup_email')
        code = form.cleaned_data['code']
        otp = OTPCode.objects.filter(email=email, code=code, is_used=False).first()
        
        if otp and not otp.is_expired: # Assuming is_expired logic or check expiry
             otp.is_used = True
             otp.save()
             messages.success(self.request, "تم التحقق بنجاح.")
             return super().form_valid(form)
        
        form.add_error('code', "رمز التحقق غير صحيح أو منتهي الصلاحية.")
        return self.form_invalid(form)


class EmailChangePasswordView(View):
    def get(self, request):
        return render(request, "auth/email_change_password.html")


class ChangePasswordView(View):
    def get(self, request):
        return render(request, "auth/change_password.html")


class VendorsView(View):
    def get(self, request):
        vendors = Vendor.objects.select_related('category').filter(is_active=True)
        return render(request, "base/vendors.html", {'vendors': vendors})


class CategoriesView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        categories = ProductCategory.objects.all()
        if query:
            categories = categories.filter(name__icontains=query)
        return render(request, "base/categories.html", {'categories': categories, 'query': query})


class ProductListView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        category_name = request.GET.get('category', '')
        min_price = request.GET.get('minPrice')
        max_price = request.GET.get('maxPrice')
        rating = request.GET.get('rating')

        products = Product.objects.select_related('tenant', 'category', 'tenant__category').filter(is_active=True)

        if query:
            products = products.filter(name__icontains=query)
        if category_name:
            products = products.filter(category__name__icontains=category_name)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if rating:
            products = products.filter(rating__gte=rating)

        categories = ProductCategory.objects.all()
        return render(request, 'base/products.html', {
            'products': products,
            'categories': categories,
            'query': query,
            'category_name': category_name,
            'min_price': min_price,
            'max_price': max_price,
            'rating': rating,
        })


class ProductDetailView(View):
    def get(self, request, product_id):
        product = Product.objects.select_related('tenant', 'category', 'tenant__category').get(id=product_id)
        return render(request, 'base/product.html', {'product': product})


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
        response['X-Toast-Message'] = "تمت إزالة المنتج من السلة"
        # response['X-Toast-Message'] = quote("تمت إزالة المنتج من السلة")
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
        response['X-Toast-Type'] = type
        return response


class RemoveFavoriteView(View):
    def post(self, request, product_id):
        fav = FavoriteService(request)
        fav.remove(product_id)
        
        response = render(request, 'components/favorites.html', fav.get_context())
        response['X-Toast-Message'] = quote("تمت إزالة المنتج من المفضلة")
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
            messages.success(request, "تم تحديث الحساب بنجاح!")
        else:
            messages.error(request, "حدث خطأ في تحديث البيانات.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

from ..forms import CheckoutForm
from ..models import Order, OrderItem
import uuid

class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = CartService(request)
        context = cart.get_context()
        if not context['grouped_items']:
            messages.warning(request, "سلتك فارغة، يرجى إضافة منتجات أولاً.")
            return redirect('home')
        
        form = CheckoutForm(initial={
            'full_name': request.user.first_name,
            'phone': request.user.phone
        })
        context['form'] = form
        return render(request, 'base/checkout.html', context)

    def post(self, request):
        cart_service = CartService(request)
        cart_data = cart_service.get_context()
        form = CheckoutForm(request.POST)
        
        if form.is_valid() and cart_data['grouped_items']:
            # Create an order for each vendor
            for vendor, data in cart_data['grouped_items'].items():
                order = Order.objects.create(
                    tenant=vendor,
                    order_number=str(uuid.uuid4()).split('-')[0].upper(),
                    total=data['subtotal'],
                    status='preparing'
                )
                
                # Create OrderItems
                for item in data['items']:
                    OrderItem.objects.create(
                        tenant=vendor,
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        price_at_order=item['product'].price
                    )
            
            # Clear individual items from DB or session
            if request.user.is_authenticated:
                from ..models import CartItem
                CartItem.objects.filter(cart__user=request.user).delete()
            else:
                request.session['cart'] = {}
            
            messages.success(request, "تم تسجيل طلبك بنجاح! شكراً لتسوقك معنا.")
            return redirect('home')
            
        messages.error(request, "يرجى التحقق من البيانات المدخلة.")
        return self.get(request)

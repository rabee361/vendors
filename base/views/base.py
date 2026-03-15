from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import FormView, View
from django.contrib.auth import login, logout, authenticate ,get_user_model
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from ..forms import *
from utils.types import UserType, CodeTypes
from utils.email import send_otp_email
from urllib.parse import quote
from ..cart import CartService
from ..favorite import FavoriteService
from ..models import *
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.mixins import VerificationRequiredMixin

User = get_user_model()


class HomeView(View):
    def get(self, request):
        if request.htmx:
            template_name = 'base/partials/products_partial.html'
        else:
            template_name = 'base/index.html'

        message_form = MessageForm

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

        vendors = Vendor.objects.select_related('category').filter(is_active=True)[:3]
        offers = Offer.objects.all()[:3]
        ads = SponsoredAd.objects.all()[:3]
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
        return super().form_valid(form)

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


class OtpCodeView(VerificationRequiredMixin,FormView):
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
        
        return super().form_valid(form)


class VerifyOtpView(VerificationRequiredMixin,FormView):
    template_name = 'auth/verify.html'
    form_class = VerifyOTPForm
    
    def get_success_url(self):
        email = self.request.session.get('signup_email')
        if email:
            try:
                user = User.objects.get(email=email)
                if user.is_seller:
                    return reverse('vendor_dashboard')
            except User.DoesNotExist:
                pass
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

class VendorDetailView(View):
    def get(self, request, vendor_id):
        vendor = Vendor.objects.get(id=vendor_id)
        return render(request, "base/store.html", {'vendor': vendor})

class CategoriesView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        categories = ProductCategory.objects.all()
        if query:
            categories = categories.filter(name__icontains=query)
        return render(request, "base/categories.html", {'categories': categories, 'query': query})


class ProductListView(View):
    def get(self, request):
        if self.request.htmx:
            template_name = 'base/partials/products_partial.html'
        else:
            template_name = 'base/products.html'

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
        return redirect(request.META.get('HTTP_REFERER', 'home'))



class CheckoutView(LoginRequiredMixin, View):
    def get(self, request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        cart = CartService(request)
        context = cart.get_context()
        
        # Filter items to only show the relevant vendor
        if vendor not in context['grouped_items']:
            return redirect('home')
            
        vendor_data = context['grouped_items'][vendor]
        context['vendor'] = vendor
        context['items'] = vendor_data['items']
        context['total'] = vendor_data['subtotal']
        
        form = CheckoutForm(initial={
            'full_name': request.user.first_name,
            'phone': request.user.phone
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
            
            # Create the order for the specific vendor
            order = Order.objects.create(
                tenant=vendor,
                order_number=str(uuid.uuid4()).split('-')[0].upper(),
                total=data['subtotal'],
                status='preparing'
            )
            
            # Create OrderItems for this vendor
            for item in data['items']:
                OrderItem.objects.create(
                    tenant=vendor,
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price_at_order=item['product'].price
                )
            
            # Clear items for THIS vendor only
            cart_service.clear_by_vendor(vendor_id)
            
            if request.htmx:
                response = redirect('home')
                response['X-Toast-Message'] = quote("تم تأكيد طلبك بنجاح! شكراً لتواصلك معنا.")
                response['X-Toast-Title'] = quote("تم الحجز")
                response['X-Toast-Type'] = "success"
                return response

            return redirect('home')
            
        return self.get(request, vendor_id)

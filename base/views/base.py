from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from ..forms import BuyerSignupForm, VendorSignupForm, BuyerLoginForm, SellerLoginForm, OTPForm, VerifyOTPForm
from ..models import Vendor, Product, ProductCategory, StoreCategory, Buyer, OTPCode
from utils.types import UserType, CodeTypes
from utils.email import send_otp_email


User = get_user_model()

class HomeView(View):
    def get(self, request):
        vendors = Vendor.objects.all()
        categories = ProductCategory.objects.all()
        products = Product.objects.all()
        return render(request, 'index.html', {'vendors': vendors, 'categories': categories, 'products': products})


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
        return render(request, "vendors.html")


class ProductListView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'products/product_list.html', {'products': products})


class ProductDetailView(View):
    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)
        return render(request, 'products/product_detail.html', {'product': product})

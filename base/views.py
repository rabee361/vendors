from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from .forms import BuyerLoginForm, SellerLoginForm, SellerRegistrationForm
from .models import Vendor, Category, Product, Deal, SponsoredAd, Order
from .decorators import seller_required

class HomeView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['deals'] = Deal.objects.filter(is_active=True).select_related('product')
        context['sponsored_ads'] = SponsoredAd.objects.filter(status='active', ad_type='section').select_related('product')
        context['products'] = Product.objects.filter(is_active=True)
        context['vendors'] = Vendor.objects.filter(is_active=True)
        return context

class BuyerLoginView(FormView):
    template_name = 'login.html'
    form_class = BuyerLoginForm
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        # Using email as username for simplicity in this boilerplate
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect('home')
        else:
            messages.error(self.request, 'Invalid email or password.')
            return self.form_invalid(form)

class SellerAuthView(TemplateView):
    template_name = 'seller-register-login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = SellerLoginForm()
        context['register_form'] = SellerRegistrationForm()
        context['categories'] = Category.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        # Determine if it's a login or registration attempt based on form fields
        if 'email' in request.POST and 'fullName' not in request.POST:
            # Login attempt
            login_form = SellerLoginForm(request.POST)
            if login_form.is_valid():
                email = login_form.cleaned_data['email']
                password = login_form.cleaned_data['password']
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('seller_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
        else:
            # Registration attempt
            register_form = SellerRegistrationForm(request.POST)
            if register_form.is_valid():
                data = register_form.cleaned_data
                user = User.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password']
                )
                user.first_name = data['full_name']
                user.save()
                
                # Find or create category
                category_name = data['store_category']
                category, created = Category.objects.get_or_create(name=category_name)
                
                Vendor.objects.create(
                    user=user,
                    store_name=data['store_name'],
                    category=category,
                    address=data['address'],
                    rating=data['rating'],
                    phone=data['phone']
                )
                
                login(request, user)
                return redirect('seller_dashboard')
                
        # If any form is invalid, re-render with context
        return self.get(request, *args, **kwargs)

@method_decorator(seller_required, name='dispatch')
class SellerDashboardView(TemplateView):
    template_name = 'seller-dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile
        context['vendor'] = vendor
        context['products'] = vendor.products.all()
        context['orders'] = Order.objects.filter(vendor=vendor)
        context['sponsored_ads'] = vendor.sponsored_ads.all()
        return context

class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Product, Offer, Order, SponsoredAd, Vendor, StoreCategory, ProductCategory
from django.views.generic import FormView
from ..forms import VendorSignupForm, ProductForm, OfferForm, SponsoredAdForm, OrderUpdateForm, ProductCategoryForm
from utils.types import UserType, CodeTypes
from utils.mixins import SellerRequiredMixin
from utils.email import send_otp_email
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class VendorDashboardView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = Vendor.objects.filter(user=request.user).first()
        
        products = Product.objects.filter(tenant=vendor).order_by('-created_at')
        offers = Offer.objects.filter(tenant=vendor).order_by('-created_at')
        ads = SponsoredAd.objects.filter(product__tenant=vendor).order_by('-created_at')
        orders = Order.objects.filter(tenant=vendor).order_by('-created_at')
        
        # Basic Stats (Fake for now as requested)
        stats = {
            'product_count': products.count(),
            'offers_count': offers.count(),
            'ads_count': ads.count(),
            'orders_count': orders.count(),
            'monthly_sales': 0,
            'visitor_growth': 0,
            'avg_rating': 0,
            'conversion_rate': 0,
        }
        
        context = {
            'vendor': vendor,
            'products': products,
            'offers': offers,
            'ads': ads,
            'orders': orders,
            'stats': stats,
        }
        
        return render(request, 'vendors/stats.html', context)

class VendorStoreView(View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, pk=pk)
        products = Product.objects.filter(tenant=vendor).order_by('-created_at')
        ads = SponsoredAd.objects.filter(product__tenant=vendor).order_by('-created_at')
        offers = Offer.objects.filter(tenant=vendor).order_by('-created_at')
        context = {
            'vendor': vendor,
            'products': products,
            'ads': ads,
            'offers': offers,
        }
        return render(request, 'vendors/store.html', context)


class VendorSignupView(FormView):
    template_name = 'auth/seller-signup.html'
    form_class = VendorSignupForm
    success_url = reverse_lazy('verify_otp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store_categories'] = StoreCategory.objects.all()
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['full_name'],
            user_type=UserType.SELLER,
        )

        # Get the StoreCategory object by name
        category_name = data['store_category']
        category = StoreCategory.objects.filter(name=category_name).first()

        vendor = Vendor.objects.create(
            user=user,
            store_name=data['store_name'],
            address=data['address'],
            phone=data['phone'],
            category=category
        )

        print("user: ", user.email)

        # Create OTP for Seller Signup
        otp_code = user.create_otp(code_type=CodeTypes.SIGNUP)
        self.request.session['signup_email'] = user.email
        
        # Send OTP Email
        # send_otp_email(otp_code, user.email)
        return redirect('verify_otp')


class ProductsListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        query = request.GET.get('q')
        products = Product.objects.filter(tenant=vendor)
        if query:
            products = products.filter(Q(name__icontains=query))
        products = products.order_by('-created_at')
        return render(request, 'vendors/products.html', {'products': products, 'stats': {'product_count': products.count()}})

class ProductAddView(SellerRequiredMixin, View):
    template_name = 'vendors/product_form.html'
    def get(self, request):
        form = ProductForm()
        return render(request, self.template_name, {'form': form, 'title': 'إضافة منتج'})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = vendor
            product.save()
            return redirect('vendor_products')
        return render(request, self.template_name, {'form': form})

class ProductUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/product_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        product = get_object_or_404(Product, pk=pk, tenant=vendor)
        form = ProductForm(instance=product)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث المنتج', 'object': product})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        product = get_object_or_404(Product, pk=pk, tenant=vendor)
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('vendor_products')
        return render(request, self.template_name, {'form': form, 'object': product})

class ProductDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        product = get_object_or_404(Product, pk=pk, tenant=vendor)
        product.delete()
        return redirect('vendor_products')

class OrdersListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        query = request.GET.get('q')
        orders = Order.objects.filter(tenant=vendor)
        if query:
            orders = orders.filter(Q(order_number__icontains=query))
        orders = orders.order_by('-created_at')
        return render(request, 'vendors/orders.html', {'orders': orders})

class OrderDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        order = get_object_or_404(Order, pk=pk, tenant=vendor)
        order.delete()
        return redirect('vendor_orders')

class OffersListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        query = request.GET.get('q')
        offers = Offer.objects.filter(tenant=vendor)
        if query:
            offers = offers.filter(Q(product__name__icontains=query))
        offers = offers.order_by('-created_at')
        return render(request, 'vendors/offers.html', {'offers': offers})

class OfferAddView(SellerRequiredMixin, View):
    template_name = 'vendors/offer_form.html' # Corrected template name
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = OfferForm()
        form.fields['product'].queryset = Product.objects.filter(tenant=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'إضافة عرض'})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.tenant = vendor
            offer.save()
            return redirect('vendor_offers')
        return render(request, self.template_name, {'form': form})

class OfferUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/offer_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        offer = get_object_or_404(Offer, pk=pk, tenant=vendor)
        form = OfferForm(instance=offer)
        form.fields['product'].queryset = Product.objects.filter(tenant=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث العرض', 'object': offer})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        offer = get_object_or_404(Offer, pk=pk, tenant=vendor)
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('vendor_offers')
        return render(request, self.template_name, {'form': form, 'object': offer})

class OfferDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        offer = get_object_or_404(Offer, pk=pk, tenant=vendor)
        offer.delete()
        return redirect('vendor_offers')

class AdsListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        query = request.GET.get('q')
        ads = SponsoredAd.objects.filter(product__tenant=vendor)
        if query:
            ads = ads.filter(Q(product__name__icontains=query))
        ads = ads.order_by('-created_at')
        return render(request, 'vendors/ads.html', {'ads': ads})

class AdAddView(SellerRequiredMixin, View):
    template_name = 'vendors/ad_form.html'
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = SponsoredAdForm()
        form.fields['product'].queryset = Product.objects.filter(tenant=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'إنشاء إعلان'})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = SponsoredAdForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.tenant = vendor
            ad.save()
            return redirect('vendor_ads')
        return render(request, self.template_name, {'form': form})

class AdUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/ad_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, product__tenant=vendor)
        form = SponsoredAdForm(instance=ad)
        form.fields['product'].queryset = Product.objects.filter(tenant=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الإعلان', 'object': ad})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, product__tenant=vendor)
        form = SponsoredAdForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.tenant = vendor
            ad.save()
            return redirect('vendor_ads')
        return render(request, self.template_name, {'form': form, 'object': ad})

class OrderUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/order_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        order = get_object_or_404(Order, pk=pk, tenant=vendor)
        form = OrderUpdateForm(instance=order)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث حالة الطلب', 'object': order})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        order = get_object_or_404(Order, pk=pk, tenant=vendor)
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('vendor_orders')
        return render(request, self.template_name, {'form': form, 'object': order})

class AdDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, tenant=vendor)
        ad.delete()
        return redirect('vendor_ads')

class StatsListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        return render(request, 'vendors/stats.html', {'vendor': vendor})

class CategoriesListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        categories = ProductCategory.objects.all().order_by('name')
        return render(request, 'vendors/categories.html', {'categories': categories})

class CategoryAddView(SellerRequiredMixin, View):
    template_name = 'vendors/category_form.html'
    def get(self, request):
        form = ProductCategoryForm()
        return render(request, self.template_name, {'form': form, 'title': 'إضافة صنف'})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = vendor
            category.save()
            return redirect('vendor_categories')
        return render(request, self.template_name, {'form': form})


class CategoryDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        category = get_object_or_404(ProductCategory, pk=pk, tenant=vendor)
        category.delete()
        return redirect('vendor_categories')


class CategoryUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/category_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        category = get_object_or_404(ProductCategory, pk=pk, tenant=vendor)
        form = ProductCategoryForm(instance=category)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الصنف', 'object': category})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        category = get_object_or_404(ProductCategory, pk=pk, tenant=vendor)
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = vendor
            category.save()
            return redirect('vendor_categories')
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الصنف', 'object': category})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        category = get_object_or_404(ProductCategory, pk=pk, product__tenant=vendor)
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = vendor
            category.save()
            return redirect('vendor_categorys')
        return render(request, self.template_name, {'form': form, 'object': category})
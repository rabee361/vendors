from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Product, Offer, Order, SponsoredAd, Vendor, StoreCategory, ProductCategory, Favorite, CartItem
from django.views.generic import FormView
from ..forms import VendorSignupForm, ProductForm, OfferForm, SponsoredAdForm, OrderUpdateForm, ProductCategoryForm
from utils.types import UserType, CodeTypes
from utils.mixins import SellerRequiredMixin
from utils.email import send_otp_email
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


from django.db.models import Sum

class VendorDashboardView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        
        products = Product.objects.filter(tenant=vendor).order_by('-created_at')
        offers = Offer.objects.filter(tenant=vendor).order_by('-created_at')
        ads = SponsoredAd.objects.filter(product__tenant=vendor).order_by('-created_at')
        orders = Order.objects.filter(tenant=vendor).order_by('-created_at')
        
        # Real Stats
        stats = {
            'product_count': products.count(),
            'categories_count': ProductCategory.objects.filter(tenant=vendor).count(),
            'orders_count': orders.count(),
            'favorites_count': Favorite.objects.filter(product__tenant=vendor).count(),
            'cart_count': CartItem.objects.filter(product__tenant=vendor).count(),
        }

        # Enhanced Stats
        top_rated = products.exclude(rating=0).order_by('-rating', '-rating_count').first()
        
        most_ordered = Product.objects.filter(tenant=vendor).annotate(
            total_sold=Sum('orderitem__quantity')
        ).filter(total_sold__gt=0).order_by('-total_sold').first()
        
        top_category = ProductCategory.objects.filter(tenant=vendor).annotate(
            total_sold=Sum('product__orderitem__quantity')
        ).filter(total_sold__gt=0).order_by('-total_sold').first()

        print(stats)
        
        context = {
            'vendor': vendor,
            'products': products,
            'offers': offers,
            'ads': ads,
            'orders': orders,
            'stats': stats,
            'enhanced_stats': {
                'top_rated': top_rated,
                'most_ordered': most_ordered,
                'top_category': top_category,
            },
            'vendor_id': vendor.id,
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
        send_otp_email(otp_code, user.email)
        return redirect('verify_otp')


class ProductsListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        query = request.GET.get('q')
        products = Product.objects.filter(tenant=vendor)
        if query:
            products = products.filter(Q(name__icontains=query))
        products = products.order_by('-created_at')
        context = {
            'weekly_views':30,
            'monthly_sales':100,
            'products': products,
            'product_count': products.count(),
            'vendor_id': vendor.id
        }
        return render(request, 'vendors/products.html', context)

class ProductAddView(SellerRequiredMixin, View):
    template_name = 'vendors/product_form.html'
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductForm(vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'إضافة منتج', 'vendor_id': vendor.id})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductForm(request.POST, request.FILES, vendor=vendor)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = vendor
            product.save()
            return redirect('vendor_products')
        return render(request, self.template_name, {'form': form, 'title': 'إضافة منتج', 'vendor_id': vendor.id})

class ProductUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/product_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        product = get_object_or_404(Product, pk=pk, tenant=vendor)
        form = ProductForm(instance=product, vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث المنتج', 'object': product, 'vendor_id': vendor.id})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        product = get_object_or_404(Product, pk=pk, tenant=vendor)
        form = ProductForm(request.POST, request.FILES, instance=product, vendor=vendor)
        if form.is_valid():
            form.save()
            return redirect('vendor_products')
        return render(request, self.template_name, {'form': form, 'object': product, 'title': 'تحديث المنتج', 'vendor_id': vendor.id})

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
        return render(request, 'vendors/orders.html', {'orders': orders, 'vendor_id': vendor.id})

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
        return render(request, 'vendors/offers.html', {'offers': offers, 'vendor_id': vendor.id})

class OfferAddView(SellerRequiredMixin, View):
    template_name = 'vendors/offer_form.html' # Corrected template name
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = OfferForm(vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'إضافة عرض', 'vendor_id': vendor.id})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = OfferForm(request.POST, vendor=vendor)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.tenant = vendor
            offer.save()
            return redirect('vendor_offers')
        return render(request, self.template_name, {'form': form, 'title': 'إضافة عرض', 'vendor_id': vendor.id})

class OfferUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/offer_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        offer = get_object_or_404(Offer, pk=pk, tenant=vendor)
        form = OfferForm(instance=offer, vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث العرض', 'object': offer, 'vendor_id': vendor.id})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        offer = get_object_or_404(Offer, pk=pk, tenant=vendor)
        form = OfferForm(request.POST, instance=offer, vendor=vendor)
        if form.is_valid():
            form.save()
            return redirect('vendor_offers')
        return render(request, self.template_name, {'form': form, 'object': offer, 'title': 'تحديث العرض', 'vendor_id': vendor.id})

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
        return render(request, 'vendors/ads.html', {'ads': ads, 'vendor_id': vendor.id})

class AdAddView(SellerRequiredMixin, View):
    template_name = 'vendors/ad_form.html'
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = SponsoredAdForm(vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'إنشاء إعلان', 'vendor_id': vendor.id})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = SponsoredAdForm(request.POST, vendor=vendor)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.tenant = vendor
            ad.save()
            return redirect('vendor_ads')
        return render(request, self.template_name, {'form': form, 'title': 'إنشاء إعلان', 'vendor_id': vendor.id})

class AdUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/ad_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, product__tenant=vendor)
        form = SponsoredAdForm(instance=ad, vendor=vendor)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الإعلان', 'object': ad, 'vendor_id': vendor.id})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, product__tenant=vendor)
        form = SponsoredAdForm(request.POST, instance=ad, vendor=vendor)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.tenant = vendor
            ad.save()
            return redirect('vendor_ads')
        return render(request, self.template_name, {'form': form, 'object': ad, 'title': 'تحديث الإعلان', 'vendor_id': vendor.id})

class OrderUpdateView(SellerRequiredMixin, View):
    template_name = 'vendors/order_form.html'
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk, tenant=vendor)
        form = OrderUpdateForm(instance=order)
        return render(request, self.template_name, {'form': form, 'title': 'تحديث حالة الطلب', 'order': order, 'vendor_id': vendor.id})

    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk, tenant=vendor)
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('vendor_orders')
        return render(request, self.template_name, {'form': form, 'order': order, 'title': 'تحديث حالة الطلب', 'vendor_id': vendor.id})

class AdDeleteView(SellerRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        ad = get_object_or_404(SponsoredAd, pk=pk, tenant=vendor)
        ad.delete()
        return redirect('vendor_ads')

class CategoriesListView(SellerRequiredMixin, View):
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        categories = ProductCategory.objects.filter(tenant=vendor).order_by('name')
        return render(request, 'vendors/categories.html', {'categories': categories, 'vendor_id': vendor.id})

class CategoryAddView(SellerRequiredMixin, View):
    template_name = 'vendors/category_form.html'
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductCategoryForm()
        return render(request, self.template_name, {'form': form, 'title': 'إضافة صنف', 'vendor_id': vendor.id})
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = vendor
            category.save()
            return redirect('vendor_categories')
        return render(request, self.template_name, {'form': form, 'title': 'إضافة صنف', 'vendor_id': vendor.id})


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
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الصنف', 'object': category, 'vendor_id': vendor.id})
    def post(self, request, pk):
        vendor = get_object_or_404(Vendor, user=request.user)
        category = get_object_or_404(ProductCategory, pk=pk, tenant=vendor)
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = vendor
            category.save()
            return redirect('vendor_categories')
        return render(request, self.template_name, {'form': form, 'title': 'تحديث الصنف', 'object': category, 'vendor_id': vendor.id})
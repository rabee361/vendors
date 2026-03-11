from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Product, Offer, Order, SponsoredAd, Vendor

class VendorDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_seller:
            return redirect('login')
            
        vendor = request.user.vendor_profile
        
        products = Product.objects.filter(tenant=vendor).order_by('-created_at')
        offers = Offer.objects.filter(tenant=vendor).order_by('-created_at')
        ads = SponsoredAd.objects.filter(product__tenant=vendor).order_by('-created_at')
        orders = Order.objects.filter(tenant=vendor).order_by('-created_at')
        
        # Basic Stats (Fake for now as requested)
        stats = {
            'product_count': products.count(),
            'weekly_views': '1,240', # Fake
            'monthly_sales': '$3,980', # Fake
            'visitor_growth': '+18%', # Fake
            'avg_rating': vendor.rating,
            'conversion_rate': '2.9%', # Fake
        }
        
        context = {
            'vendor': vendor,
            'products': products,
            'offers': offers,
            'ads': ads,
            'orders': orders,
            'stats': stats,
        }
        
        return render(request, 'vendors/seller-dashboard.html', context)

class VendorStoreView(TemplateView):
    template_name = 'vendors/store.html'

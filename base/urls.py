from django.urls import include
from django.urls import path
from .views import base

basePatterns = [
    path('', base.HomeView.as_view(), name='home'),
    path('login/', base.LoginView.as_view(), name='login'),
    path('logout/', base.LogoutView.as_view(), name='logout'),
    path('signup/', base.BuyerSignupView.as_view(), name='buyer_signup'),
    path('otp/', base.OtpCodeView.as_view(), name='otp'),
    path('verify-otp/', base.VerifyOtpView.as_view(), name='verify_otp'),
    path('vendors/', base.VendorsView.as_view(), name='vendors'),
]

moderatorPatterns = [
    # path('dashboard/', base.ModeratorDashboardView.as_view(), name='moderator_dashboard'),
]

vendorPatterns = [
    # path('auth/login', views.base.vendor_auth_view.as_view(), name='vendor_auth'),
    # path('auth/logout', views.base.vendor_auth_view.as_view(), name='vendor_auth'),
    # path('auth/signup', views.base.vendor_auth_view.as_view(), name='vendor_auth'),
    # path('dashboard', views.base.vendor_dashboard_view.as_view(), name='vendor_dashboard'),
    path('signup/', base.VendorSignupView.as_view(), name='vendor_signup'),
    path('products/', base.ProductListView.as_view(), name='product_list'),
    path('products/<int:product_id>/', base.ProductDetailView.as_view(), name='product'),
] 

urlpatterns = [
    path('', include(basePatterns)),
    path('moderator/', include(moderatorPatterns)),
    path('vendor/', include(vendorPatterns))
]

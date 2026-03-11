from django.urls import include
from django.urls import path
from .views import base, moderators, vendor


basePatterns = [
    path('', base.HomeView.as_view(), name='home'),
    path('login/', base.LoginView.as_view(), name='login'),
    path('logout/', base.LogoutView.as_view(), name='logout'),
    path('signup/', base.BuyerSignupView.as_view(), name='buyer_signup'),
    path('otp/', base.OtpCodeView.as_view(), name='otp'),
    path('verify-otp/', base.VerifyOtpView.as_view(), name='verify_otp'),
    path('vendors/', base.VendorsView.as_view(), name='vendors'),
    path('categories/', base.CategoriesView.as_view(), name='category_list'),
    path('products/', base.ProductListView.as_view(), name='product_list'),
    path('products/<int:product_id>/', base.ProductDetailView.as_view(), name='product'),
    path('cart/', base.CartHTMXView.as_view(), name='cart_htmx'),
    path('cart/add/<int:product_id>/', base.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:product_id>/', base.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/update/<int:product_id>/', base.UpdateCartView.as_view(), name='update_cart'),
    path('favorites/toggle/<int:product_id>/', base.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('favorites/remove/<int:product_id>/', base.RemoveFavoriteView.as_view(), name='remove_favorite'),
    path('account/update/', base.AccountUpdateView.as_view(), name='account_update'),
    path('change-password/', base.ChangePasswordView.as_view(), name='change_password'),
    path('checkout/', base.CheckoutView.as_view(), name='checkout'),
]

moderatorPatterns = [
    path('vendors/', moderators.ModeratorVendorsView.as_view(), name='moderator_vendors'),
    path('stats/', moderators.ModeratorStatsView.as_view(), name='moderator_stats'),
    path('list/', moderators.ModeratorListView.as_view(), name='moderator_list'),
    path('add/', moderators.ModeratorAddView.as_view(), name='moderator_add'),
    path('update/<int:pk>/', moderators.ModeratorUpdateView.as_view(), name='moderator_update'),
    path('delete/<int:pk>/', moderators.ModeratorDeleteView.as_view(), name='moderator_delete'),
]

vendorPatterns = [
    path('dashboard/', vendor.VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('store/', vendor.VendorStoreView.as_view(), name='vendor_store'),
    path('signup/', base.VendorSignupView.as_view(), name='vendor_signup'),
] 

urlpatterns = [
    path('', include(basePatterns)),
    path('moderator/', include(moderatorPatterns)),
    path('vendor/', include(vendorPatterns))
]

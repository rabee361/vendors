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
    path('vendors/<int:vendor_id>/', base.VendorDetailView.as_view(), name='vendor'),
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
    path('checkout/<int:vendor_id>/', base.CheckoutView.as_view(), name='checkout'),
]

moderatorPatterns = [
    path('', moderators.ModeratorStatsView.as_view(), name='moderator_stats'),
    path('vendors/', moderators.ModeratorVendorsView.as_view(), name='moderator_vendors'),
    path('list/', moderators.ModeratorListView.as_view(), name='moderator_list'),
    path('update/<int:pk>/', moderators.ModeratorUpdateView.as_view(), name='moderator_update'),
    path('categories/', moderators.ModeratorCategoriesView.as_view(), name='moderator_categories'),
    path('add/', moderators.ModeratorAddView.as_view(), name='moderator_add'),
    path('delete/<int:pk>/', moderators.ModeratorDeleteView.as_view(), name='moderator_delete'),
    path('categories/add/', moderators.ModeratorCategoryAddView.as_view(), name='category_add'),
    path('categories/update/<int:pk>/', moderators.ModeratorCategoryUpdateView.as_view(), name='category_update'),
    path('categories/delete/<int:pk>/', moderators.ModeratorCategoryDeleteView.as_view(), name='category_delete'),
]

vendorPatterns = [
    path('dashboard/', vendor.VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('offers/', vendor.OffersListView.as_view(), name='vendor_offers'),
    path('offers/add/', vendor.OfferAddView.as_view(), name='offer_add'),
    path('offers/update/<int:pk>/', vendor.OfferUpdateView.as_view(), name='offer_update'),
    path('offers/delete/<int:pk>/', vendor.OfferDeleteView.as_view(), name='offer_delete'),
    path('ads/', vendor.AdsListView.as_view(), name='vendor_ads'),
    path('ads/add/', vendor.AdAddView.as_view(), name='ad_add'),
    path('ads/update/<int:pk>/', vendor.AdUpdateView.as_view(), name='ad_update'),
    path('ads/delete/<int:pk>/', vendor.AdDeleteView.as_view(), name='ad_delete'),
    path('products/', vendor.ProductsListView.as_view(), name='vendor_products'),
    path('products/add/', vendor.ProductAddView.as_view(), name='product_add'),
    path('products/update/<int:pk>/', vendor.ProductUpdateView.as_view(), name='product_update'),
    path('products/delete/<int:pk>/', vendor.ProductDeleteView.as_view(), name='product_delete'),
    path('orders/', vendor.OrdersListView.as_view(), name='vendor_orders'),
    path('orders/update/<int:pk>/', vendor.OrderUpdateView.as_view(), name='order_update'),
    path('orders/delete/<int:pk>/', vendor.OrderDeleteView.as_view(), name='order_delete'),
    path('stats/', vendor.StatsListView.as_view(), name='vendor_stats'),
    path('store/<int:pk>/', vendor.VendorStoreView.as_view(), name='vendor_store'),
    path('signup/', vendor.VendorSignupView.as_view(), name='vendor_signup'),
]

urlpatterns = [
    path('', include(basePatterns)),
    path('moderator/', include(moderatorPatterns)),
    path('vendor/', include(vendorPatterns))
]

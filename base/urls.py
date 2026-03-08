from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view.as_view(), name='home'),
    path('login/', views.buyer_login_view.as_view(), name='login'),
    path('seller/auth/', views.seller_auth_view.as_view(), name='seller_auth'),
    path('seller/dashboard/', views.seller_dashboard_view.as_view(), name='seller_dashboard'),
    path('logout/', views.logout_view.as_view(), name='logout'),
]

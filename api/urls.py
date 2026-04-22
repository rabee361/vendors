from django.urls import path
from .views import APILoginAPIView, OrderCreateAPIView, ProductListAPIView, HasTelegramAPIView

app_name = 'api'

urlpatterns = [
	path('login/', APILoginAPIView.as_view(), name='login'),
	path('users/has-telegram/' , HasTelegramAPIView.as_view(), name='has-telegram'),
	path('products/', ProductListAPIView.as_view(), name='product-list'),
	path('orders/', OrderCreateAPIView.as_view(), name='order-create'),
]

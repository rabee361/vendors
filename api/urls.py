from django.urls import path
from .views import APILoginAPIView, OrderCreateAPIView, ProductListAPIView

app_name = 'api'

urlpatterns = [
	path('login/', APILoginAPIView.as_view(), name='login'),
	path('products/', ProductListAPIView.as_view(), name='product-list'),
	path('orders/', OrderCreateAPIView.as_view(), name='order-create'),
]

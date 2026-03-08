from django.contrib import admin
from .models import (
    Category, Vendor, Product, Deal, SponsoredAd, 
    Cart, CartItem, Favorite, Order, OrderItem, 
    ContactMessage, VendorStats
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'category', 'rating', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('store_name', 'user__username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'price', 'stock', 'category', 'is_active', 'is_sponsored_badge')
    list_filter = ('category', 'is_active', 'is_sponsored_badge', 'vendor')
    search_fields = ('name', 'vendor__store_name')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(SponsoredAd)
class SponsoredAdAdmin(admin.ModelAdmin):
    list_display = ('product', 'vendor', 'ad_type', 'budget', 'status', 'start_date')
    list_filter = ('ad_type', 'status')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'created_at')
    inlines = [CartItemInline]

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'buyer', 'vendor', 'total', 'status', 'created_at')
    list_filter = ('status', 'vendor')
    search_fields = ('order_number', 'buyer__username')
    inlines = [OrderItemInline]

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_read', 'created_at')
    list_filter = ('is_read',)

@admin.register(VendorStats)
class VendorStatsAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'week_start', 'views', 'sales_total')

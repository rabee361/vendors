from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Buyer, AdminUser,
    ProductCategory, Vendor, Product, Deal, SponsoredAd, 
    Cart, CartItem, Favorite, Order, OrderItem, 
    ContactMessage, VendorStats, StoreCategory, OTPCode
)

class BuyerInline(admin.StackedInline):
    model = Buyer
    can_delete = False

class VendorInline(admin.StackedInline):
    model = Vendor
    can_delete = False

class AdminUserInline(admin.StackedInline):
    model = AdminUser
    can_delete = False


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_superuser')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    inlines = [BuyerInline, VendorInline, AdminUserInline]

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'managed_domain', 'created_at')
    search_fields = ('user__username', 'managed_domain')

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'slug', 'created_at')
    list_filter = ('tenant',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'category', 'rating', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('store_name', 'user__username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'price', 'stock', 'category', 'is_active', 'is_sponsored_badge')
    list_filter = ('category', 'is_active', 'is_sponsored_badge', 'tenant')
    search_fields = ('name', 'tenant__store_name')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

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
    list_display = ('order_number', 'tenant', 'total', 'status', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('order_number', 'items__product__name')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_order', 'tenant')
    list_filter = ('tenant',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'tenant', 'is_read', 'created_at')
    list_filter = ('is_read', 'tenant')

@admin.register(VendorStats)
class VendorStatsAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'week_start', 'views', 'sales_total')
    list_filter = ('tenant',)

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'code_type', 'is_used', 'created_at', 'expires_at')
    list_filter = ('code_type', 'is_used')
    search_fields = ('email', 'code')

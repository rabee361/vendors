from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class BuyerInline(admin.StackedInline):
    model = Buyer
    can_delete = False

class VendorInline(admin.StackedInline):
    model = Vendor
    can_delete = False

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id','username', 'email', 'user_type', 'is_staff', 'is_superuser', 'is_verified','telegram_id')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_verified')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type', 'is_verified', 'telegram_id')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type', 'is_verified', 'telegram_id')}),
    )
    inlines = [BuyerInline, VendorInline]

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'tenant', 'slug', 'created_at')
    list_filter = ('tenant',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductEmbedding)
class ProductEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('id','product', 'model_name', 'created_at')

@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id','source_product', 'recommended_product', 'score', 'rank', 'generated_at')

@admin.register(UserRecommendation)
class UserRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'product', 'score', 'rank', 'generated_at')

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('id','store_name', 'user', 'category')
    list_filter = ('category',)
    search_fields = ('store_name', 'user__username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'tenant', 'price', 'stock', 'category', 'is_active', 'is_sponsored_badge')
    list_filter = ('category', 'is_active', 'is_sponsored_badge', 'tenant')
    search_fields = ('name', 'tenant__store_name')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id','product', 'discount', 'start_date', 'end_date', 'is_active')
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
    list_display = ('id','user', 'product', 'added_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','order_number', 'tenant', 'total', 'status', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('order_number', 'items__product__name')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id','order', 'product', 'quantity', 'price_at_order', 'tenant')
    list_filter = ('tenant',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'email', 'created_at')

@admin.register(VendorStats)
class VendorStatsAdmin(admin.ModelAdmin):
    list_display = ('id','tenant', 'week_start', 'views', 'sales_total')
    list_filter = ('tenant',)

@admin.register(SponsoredAd)
class SponsoredAdAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'ad_type', 'status', 'start_date', 'end_date', 'budget')
    list_filter = ('ad_type', 'status')
    search_fields = ('product__name', 'tenant__store_name')

@admin.register(SponsoredAdClick)
class SponsoredAdClickAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'user', 'visitor_token', 'source_page', 'created_at')
    list_filter = ('source_page', 'created_at')
    search_fields = ('ad__product__name', 'user__email', 'visitor_token')

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('id','email', 'code', 'code_type', 'is_used', 'created_at', 'expires_at')
    list_filter = ('code_type', 'is_used')
    search_fields = ('email', 'code')

@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__username', 'product__name')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'value', 'created_at')

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value')


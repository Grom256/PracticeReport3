from django.contrib import admin

from .models import Category, Product, StockNotification, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'owner', 'product_type', 'category', 'price', 'stock_quantity', 'is_rare', 'is_active'
    )
    list_filter = ('product_type', 'category', 'condition', 'is_rare', 'is_active')
    search_fields = ('name', 'sku', 'series', 'owner__username')
    list_editable = ('price', 'stock_quantity', 'is_active')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name', 'product__sku')


@admin.register(StockNotification)
class StockNotificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'channel', 'email', 'telegram_chat_id', 'is_notified', 'created_at')
    list_filter = ('channel', 'is_notified', 'created_at')
    search_fields = ('product__name', 'product__sku', 'user__username', 'email', 'telegram_chat_id')

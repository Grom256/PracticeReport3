from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'product_type', 'category', 'price', 'stock_quantity', 'is_rare', 'is_active'
    )
    list_filter = ('product_type', 'category', 'condition', 'is_rare', 'is_active')
    search_fields = ('name', 'sku', 'series')
    list_editable = ('price', 'stock_quantity', 'is_active')

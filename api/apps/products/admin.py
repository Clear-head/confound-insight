from django.contrib import admin
from .models import Product, ProductIngredient



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'permit_number', 'manufacturer', 'is_combination', 'created_at']
    list_filter = ['is_combination', 'manufacturer', 'source']
    search_fields = ['product_name', 'permit_number', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('product_name', 'permit_number', 'manufacturer', 'is_combination')
        }),
        ('메타데이터', {
            'fields': ('source', 'last_synced_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = ['product', 'raw_ingredient_name', 'compound', 'normalization_status', 'is_main_active']
    list_filter = ['normalization_status', 'is_main_active', 'ingredient_type']
    search_fields = ['raw_ingredient_name', 'product__product_name']
    autocomplete_fields = ['product', 'compound']
    readonly_fields = ['created_at', 'updated_at']
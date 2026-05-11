from django.contrib import admin
from .models import (
    Brand, ScentType, Product, ProductVariant, 
    Order, Comment, OrderItem, Cart, CartItem
)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'gender')
    list_filter = ('brand', 'gender', 'scent_type')
    search_fields = ('name', 'description')
    inlines = [ProductVariantInline]  

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
admin.site.register(Brand)
admin.site.register(ScentType)
admin.site.register(Comment)
admin.site.register(Cart)
admin.site.register(CartItem)
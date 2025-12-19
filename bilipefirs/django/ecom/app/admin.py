from django.contrib import admin
from .models import Cart, Product, Customer ,CryptoPayment,OrderPlaced,OrderItem,Order,send_order_email
from .models import DiscountCode

from django.contrib import admin
from django.utils.html import format_html

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'discount_percentage', 
        'is_active',
        'valid_until',
        'usage_status',
        'minimum_order_amount'
    )
    list_filter = ('is_active', 'valid_until')
    search_fields = ('code',)
    readonly_fields = ('current_uses',)
    
    def usage_status(self, obj):
        if not obj.max_uses:
            return 'Unlimited'
        percentage = (obj.current_uses / obj.max_uses) * 100
        color = 'green' if percentage < 80 else 'orange' if percentage < 90 else 'red'
        return format_html(
            '<span style="color: {};">{}/{} ({:.0f}%)</span>',
            color,
            obj.current_uses,
            obj.max_uses,
            percentage
        )
    
    usage_status.short_description = 'Usage'

    
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'category']
     
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'house_no', 'street', 'city', 'pincode', 'state']
    list_filter = ['state', 'city']
    search_fields = ['full_name', 'house_no', 'street', 'city', 'state', 'pincode']
    list_per_page = 20
    
@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity'] 


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'product', 'quantity']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity']
    list_filter = ['order__status']
    search_fields = ['order__id', 'product__title']

@admin.register(CryptoPayment)
class CryptoPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_hash', 'user', 'order', 'amount', 'eth_amount', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['transaction_hash', 'from_address', 'user__username']
    readonly_fields = ['timestamp']

@admin.register(OrderPlaced)
class OrderPlacedAdmin(admin.ModelAdmin):
    list_display = ['user', 'customer', 'product', 'quantity', 'ordered_date', 'status']
    list_filter = ['status', 'ordered_date']
    search_fields = ['user__username', 'customer__name', 'product__title']
    readonly_fields = ['ordered_date']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'customer__name']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        if change:
            order_items = OrderItem.objects.filter(order=obj)
            subject = f"Order {obj.id} Status Changed"
            send_order_email(obj.user.email, subject, obj, order_items)
        super().save_model(request, obj, form, change)

admin.site.register(Order, OrderAdmin)
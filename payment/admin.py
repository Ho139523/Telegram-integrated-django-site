from django.contrib import admin
from .models import Transaction, Sale, Cart, CartItem

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "profile", "amount", "status", "created_at")
    readonly_fields = ("transaction_id", "amount", "status")
    list_filter = ('status',)
    ordering = ['created_at']
    search_fields = ["transaction_id"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', "is_released", 'seller', 'quantity', 'total_price', 'created_at', 'transaction')
    list_filter = ('product', 'seller', 'transaction')
    ordering = ['created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('profile', 'created_at')
    list_filter = ('profile', )
    ordering = ['created_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'get_total_price')

    def get_total_price(self, obj):
        return obj.total_price()
    
    get_total_price.short_description = "Total Price"

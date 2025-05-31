from django.contrib import admin
from .models import Transaction, Sale

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'cart', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    ordering = ['created_at']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'seller', 'transaction', 'quantity', 'total_price', 'created_at')
    list_filter = ('product', 'seller', 'transaction')
    ordering = ['created_at']
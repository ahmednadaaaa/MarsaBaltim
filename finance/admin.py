from django.contrib import admin
from .models import Income, Expense

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'payment_method', 'category', 'date', 'booking')
    list_filter = ('payment_method', 'category', 'date')
    search_fields = ('title', 'source', 'note')
    date_hierarchy = 'date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'payment_method', 'category', 'date', 'property', 'booking')
    list_filter = ('payment_method', 'category', 'date')
    search_fields = ('title', 'note')
    date_hierarchy = 'date'

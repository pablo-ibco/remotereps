"""
Django admin for brands app.
"""

from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Admin interface for Brand model."""
    
    list_display = [
        'name', 
        'daily_budget', 
        'monthly_budget', 
        'total_daily_spend_display',
        'total_monthly_spend_display',
        'daily_remaining_display',
        'monthly_remaining_display',
        'created_at'
    ]
    
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'daily_budget', 'monthly_budget')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_daily_spend_display(self, obj: Brand) -> str:
        """Display total daily spend with color coding."""
        total = obj.get_total_daily_spend()
        percentage = (total / obj.daily_budget) * 100 if obj.daily_budget > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">${:.2f} ({:.1f}%)</span>',
            color, total, percentage
        )
    total_daily_spend_display.short_description = 'Total Daily Spend'
    
    def total_monthly_spend_display(self, obj: Brand) -> str:
        """Display total monthly spend with color coding."""
        total = obj.get_total_monthly_spend()
        percentage = (total / obj.monthly_budget) * 100 if obj.monthly_budget > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">${:.2f} ({:.1f}%)</span>',
            color, total, percentage
        )
    total_monthly_spend_display.short_description = 'Total Monthly Spend'
    
    def daily_remaining_display(self, obj: Brand) -> str:
        """Display remaining daily budget."""
        remaining = obj.get_remaining_daily_budget()
        color = 'green' if remaining > 0 else 'red'
        
        return format_html(
            '<span style="color: {};">${:.2f}</span>',
            color, remaining
        )
    daily_remaining_display.short_description = 'Daily Remaining'
    
    def monthly_remaining_display(self, obj: Brand) -> str:
        """Display remaining monthly budget."""
        remaining = obj.get_remaining_monthly_budget()
        color = 'green' if remaining > 0 else 'red'
        
        return format_html(
            '<span style="color: {};">${:.2f}</span>',
            color, remaining
        )
    monthly_remaining_display.short_description = 'Monthly Remaining'

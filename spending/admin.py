"""
Django admin for spending app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Spend, SpendType


@admin.register(Spend)
class SpendAdmin(admin.ModelAdmin):
    """Admin interface for Spend model."""
    
    list_display = [
        'campaign_link',
        'brand_link',
        'amount_display',
        'spend_date',
        'spend_type',
        'description',
        'created_at'
    ]
    
    list_filter = [
        'spend_type',
        'spend_date',
        'campaign__brand',
        'created_at'
    ]
    
    search_fields = [
        'campaign__name',
        'campaign__brand__name',
        'description'
    ]
    
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Spend Information', {
            'fields': ('campaign', 'amount', 'spend_date', 'spend_type', 'description')
        }),
        ('System Information', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def campaign_link(self, obj: Spend) -> str:
        """Display campaign as a link."""
        if obj.campaign:
            url = reverse('admin:campaigns_campaign_change', args=[obj.campaign.id])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.name)
        return '-'
    campaign_link.short_description = 'Campaign'
    campaign_link.admin_order_field = 'campaign__name'
    
    def brand_link(self, obj: Spend) -> str:
        """Display brand as a link."""
        if obj.campaign and obj.campaign.brand:
            url = reverse('admin:brands_brand_change', args=[obj.campaign.brand.id])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.brand.name)
        return '-'
    brand_link.short_description = 'Brand'
    brand_link.admin_order_field = 'campaign__brand__name'
    
    def amount_display(self, obj: Spend) -> str:
        """Display amount with currency formatting."""
        return format_html('<strong>${:.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'

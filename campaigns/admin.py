"""
Django admin for campaigns app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Campaign, CampaignStatus, PauseReason


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaign model."""
    
    list_display = [
        'name',
        'brand_link',
        'status_display',
        'daily_spend_display',
        'monthly_spend_display',
        'pause_reason_display',
        'paused_at',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'pause_reason',
        'brand',
        'created_at',
        'paused_at'
    ]
    
    search_fields = ['name', 'brand__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'name')
        }),
        ('Status & Budget', {
            'fields': ('status', 'pause_reason', 'paused_at', 'daily_spend', 'monthly_spend')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_campaigns', 'pause_campaigns', 'reset_daily_spends', 'reset_monthly_spends']
    
    def brand_link(self, obj: Campaign) -> str:
        """Display brand as a link."""
        if obj.brand:
            url = reverse('admin:brands_brand_change', args=[obj.brand.id])
            return format_html('<a href="{}">{}</a>', url, obj.brand.name)
        return '-'
    brand_link.short_description = 'Brand'
    brand_link.admin_order_field = 'brand__name'
    
    def status_display(self, obj: Campaign) -> str:
        """Display status with color coding."""
        if obj.status == CampaignStatus.ACTIVE:
            return format_html('<span style="color: green;">● Active</span>')
        else:
            return format_html('<span style="color: red;">● Paused</span>')
    status_display.short_description = 'Status'
    
    def daily_spend_display(self, obj: Campaign) -> str:
        """Display daily spend with color coding."""
        percentage = (obj.daily_spend / obj.brand.daily_budget) * 100 if obj.brand.daily_budget > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">${:.2f} ({:.1f}%)</span>',
            color, obj.daily_spend, percentage
        )
    daily_spend_display.short_description = 'Daily Spend'
    daily_spend_display.admin_order_field = 'daily_spend'
    
    def monthly_spend_display(self, obj: Campaign) -> str:
        """Display monthly spend with color coding."""
        percentage = (obj.monthly_spend / obj.brand.monthly_budget) * 100 if obj.brand.monthly_budget > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">${:.2f} ({:.1f}%)</span>',
            color, obj.monthly_spend, percentage
        )
    monthly_spend_display.short_description = 'Monthly Spend'
    monthly_spend_display.admin_order_field = 'monthly_spend'
    
    def pause_reason_display(self, obj: Campaign) -> str:
        """Display pause reason."""
        if obj.pause_reason:
            return obj.get_pause_reason_display()
        return '-'
    pause_reason_display.short_description = 'Pause Reason'
    
    def activate_campaigns(self, request, queryset) -> None:
        """Admin action to activate selected campaigns."""
        activated = 0
        for campaign in queryset:
            if campaign.activate():
                activated += 1
        
        self.message_user(
            request,
            f'Successfully activated {activated} out of {queryset.count()} campaigns.'
        )
    activate_campaigns.short_description = "Activate selected campaigns"
    
    def pause_campaigns(self, request, queryset) -> None:
        """Admin action to pause selected campaigns."""
        for campaign in queryset:
            campaign.pause(PauseReason.MANUAL)
        
        self.message_user(
            request,
            f'Successfully paused {queryset.count()} campaigns.'
        )
    pause_campaigns.short_description = "Pause selected campaigns"
    
    def reset_daily_spends(self, request, queryset) -> None:
        """Admin action to reset daily spends for selected campaigns."""
        for campaign in queryset:
            campaign.reset_daily_spend()
        
        self.message_user(
            request,
            f'Successfully reset daily spends for {queryset.count()} campaigns.'
        )
    reset_daily_spends.short_description = "Reset daily spends"
    
    def reset_monthly_spends(self, request, queryset) -> None:
        """Admin action to reset monthly spends for selected campaigns."""
        for campaign in queryset:
            campaign.reset_monthly_spend()
        
        self.message_user(
            request,
            f'Successfully reset monthly spends for {queryset.count()} campaigns.'
        )
    reset_monthly_spends.short_description = "Reset monthly spends"

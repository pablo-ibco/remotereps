"""
Django admin for scheduling app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Schedule, DayOfWeek


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """Admin interface for Schedule model."""
    
    list_display = [
        'campaign_link',
        'brand_link',
        'day_of_week',
        'time_range_display',
        'is_active_display',
        'created_at'
    ]
    
    list_filter = [
        'day_of_week',
        'is_active',
        'campaign__brand',
        'created_at'
    ]
    
    search_fields = [
        'campaign__name',
        'campaign__brand__name'
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('campaign', 'day_of_week', 'start_time', 'end_time', 'is_active')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_schedules', 'deactivate_schedules']
    
    def campaign_link(self, obj: Schedule) -> str:
        """Display campaign as a link."""
        if obj.campaign:
            url = reverse('admin:campaigns_campaign_change', args=[obj.campaign.id])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.name)
        return '-'
    campaign_link.short_description = 'Campaign'
    campaign_link.admin_order_field = 'campaign__name'
    
    def brand_link(self, obj: Schedule) -> str:
        """Display brand as a link."""
        if obj.campaign and obj.campaign.brand:
            url = reverse('admin:brands_brand_change', args=[obj.campaign.brand.id])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.brand.name)
        return '-'
    brand_link.short_description = 'Brand'
    brand_link.admin_order_field = 'campaign__brand__name'
    
    def time_range_display(self, obj: Schedule) -> str:
        """Display time range."""
        return format_html(
            '<strong>{} - {}</strong>',
            obj.start_time.strftime('%H:%M'),
            obj.end_time.strftime('%H:%M')
        )
    time_range_display.short_description = 'Time Range'
    
    def is_active_display(self, obj: Schedule) -> str:
        """Display active status with color coding."""
        if obj.is_active:
            return format_html('<span style="color: green;">● Active</span>')
        else:
            return format_html('<span style="color: red;">● Inactive</span>')
    is_active_display.short_description = 'Status'
    
    def activate_schedules(self, request, queryset) -> None:
        """Admin action to activate selected schedules."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} schedules.'
        )
    activate_schedules.short_description = "Activate selected schedules"
    
    def deactivate_schedules(self, request, queryset) -> None:
        """Admin action to deactivate selected schedules."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} schedules.'
        )
    deactivate_schedules.short_description = "Deactivate selected schedules"

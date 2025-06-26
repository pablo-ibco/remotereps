"""
Views for campaigns app.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from typing import Dict, List
from .models import Campaign, CampaignStatus, PauseReason


def campaign_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view for campaigns overview."""
    campaigns = Campaign.objects.all().select_related('brand')
    
    # Calculate summary statistics
    total_campaigns = campaigns.count()
    active_campaigns = campaigns.filter(status=CampaignStatus.ACTIVE).count()
    paused_campaigns = campaigns.filter(status=CampaignStatus.PAUSED).count()
    total_daily_spend = sum(campaign.daily_spend for campaign in campaigns)
    total_monthly_spend = sum(campaign.monthly_spend for campaign in campaigns)
    
    # Group by pause reason
    pause_reasons: Dict[str, int] = {}
    for campaign in campaigns.filter(status=CampaignStatus.PAUSED):
        reason = campaign.pause_reason or 'Unknown'
        pause_reasons[reason] = pause_reasons.get(reason, 0) + 1
    
    context = {
        'campaigns': campaigns,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'paused_campaigns': paused_campaigns,
        'total_daily_spend': total_daily_spend,
        'total_monthly_spend': total_monthly_spend,
        'pause_reasons': pause_reasons,
    }
    
    return render(request, 'campaigns/dashboard.html', context)


def campaign_detail(request: HttpRequest, campaign_id: str) -> HttpResponse:
    """Detail view for a specific campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Get recent spends
    recent_spends = campaign.spends.all().order_by('-spend_date')[:10]
    
    # Get schedules
    schedules = campaign.schedules.all().order_by('day_of_week', 'start_time')
    
    context = {
        'campaign': campaign,
        'recent_spends': recent_spends,
        'schedules': schedules,
        'remaining_daily_budget': campaign.get_remaining_daily_budget(),
        'remaining_monthly_budget': campaign.get_remaining_monthly_budget(),
        'daily_budget_percentage': float((campaign.daily_spend / campaign.brand.daily_budget) * 100),
        'monthly_budget_percentage': float((campaign.monthly_spend / campaign.brand.monthly_budget) * 100),
    }
    
    return render(request, 'campaigns/detail.html', context)


def campaign_stats_api(request: HttpRequest, campaign_id: str) -> JsonResponse:
    """API endpoint for campaign statistics."""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    stats = {
        'id': str(campaign.id),
        'name': campaign.name,
        'brand_name': campaign.brand.name,
        'status': campaign.status,
        'pause_reason': campaign.pause_reason,
        'daily_spend': float(campaign.daily_spend),
        'monthly_spend': float(campaign.monthly_spend),
        'daily_budget': float(campaign.brand.daily_budget),
        'monthly_budget': float(campaign.brand.monthly_budget),
        'remaining_daily_budget': float(campaign.get_remaining_daily_budget()),
        'remaining_monthly_budget': float(campaign.get_remaining_monthly_budget()),
        'daily_budget_percentage': float((campaign.daily_spend / campaign.brand.daily_budget) * 100),
        'monthly_budget_percentage': float((campaign.monthly_spend / campaign.brand.monthly_budget) * 100),
        'is_active': campaign.is_active(),
        'is_paused': campaign.is_paused(),
        'can_be_activated': campaign.can_be_activated(),
    }
    
    return JsonResponse(stats)


def campaign_status_summary(request: HttpRequest) -> HttpResponse:
    """Summary view of campaign statuses."""
    campaigns = Campaign.objects.all().select_related('brand')
    
    # Group campaigns by status
    status_summary = {
        'active': campaigns.filter(status=CampaignStatus.ACTIVE),
        'paused': campaigns.filter(status=CampaignStatus.PAUSED),
    }
    
    # Group paused campaigns by reason
    pause_reasons: Dict[str, List[Campaign]] = {}
    for campaign in status_summary['paused']:
        reason = campaign.pause_reason or 'Unknown'
        if reason not in pause_reasons:
            pause_reasons[reason] = []
        pause_reasons[reason].append(campaign)
    
    context = {
        'status_summary': status_summary,
        'pause_reasons': pause_reasons,
        'total_campaigns': campaigns.count(),
    }
    
    return render(request, 'campaigns/status_summary.html', context)

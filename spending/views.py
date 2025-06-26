"""
Views for spending app.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest
from django.db.models import Sum, Avg, Count
from datetime import date, timedelta
from .models import Spend, SpendType
from .services import SpendingService
from brands.models import Brand
from campaigns.models import Campaign
from typing import Any


def spending_dashboard(request: HttpRequest) -> Any:
    """Dashboard view for spending overview."""
    # Get spending statistics
    total_spends = Spend.objects.count()
    total_amount = Spend.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get today's spending
    today = date.today()
    today_spends = Spend.objects.filter(spend_date=today)
    today_amount = today_spends.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get this month's spending
    current_month = today.month
    current_year = today.year
    month_spends = Spend.objects.filter(
        spend_date__year=current_year,
        spend_date__month=current_month
    )
    month_amount = month_spends.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get spending by type
    daily_spends = Spend.objects.filter(spend_type=SpendType.DAILY)
    monthly_spends = Spend.objects.filter(spend_type=SpendType.MONTHLY)
    
    daily_amount = daily_spends.aggregate(total=Sum('amount'))['total'] or 0
    monthly_amount = monthly_spends.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get recent spends
    recent_spends = Spend.objects.select_related('campaign__brand').order_by('-spend_date')[:10]
    
    # Get top spending campaigns
    top_campaigns = Campaign.objects.annotate(
        total_spend=Sum('spends__amount')
    ).filter(total_spend__isnull=False).order_by('-total_spend')[:5]
    
    context = {
        'total_spends': total_spends,
        'total_amount': total_amount,
        'today_amount': today_amount,
        'month_amount': month_amount,
        'daily_amount': daily_amount,
        'monthly_amount': monthly_amount,
        'recent_spends': recent_spends,
        'top_campaigns': top_campaigns,
        'today': today,
    }
    
    return render(request, 'spending/dashboard.html', context)


def spending_analytics(request: HttpRequest) -> Any:
    """Analytics view for spending patterns."""
    # Get date range from request (default to last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get spending data for the period
    spends = Spend.objects.filter(
        spend_date__gte=start_date,
        spend_date__lte=end_date
    ).select_related('campaign__brand')
    
    # Daily spending breakdown
    daily_breakdown = spends.values('spend_date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('spend_date')
    
    # Spending by campaign
    campaign_breakdown = spends.values(
        'campaign__name', 'campaign__brand__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Spending by brand
    brand_breakdown = spends.values('campaign__brand__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Spending by type
    type_breakdown = spends.values('spend_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'days': days,
        'total_spends': spends.count(),
        'total_amount': spends.aggregate(total=Sum('amount'))['total'] or 0,
        'daily_breakdown': daily_breakdown,
        'campaign_breakdown': campaign_breakdown,
        'brand_breakdown': brand_breakdown,
        'type_breakdown': type_breakdown,
    }
    
    return render(request, 'spending/analytics.html', context)


def campaign_spending_detail(request: HttpRequest, campaign_id: str) -> Any:
    """Detail view for campaign spending."""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Get all spends for this campaign
    spends = campaign.spends.all().order_by('-spend_date')
    
    # Get spending statistics
    total_spends = spends.count()
    total_amount = spends.aggregate(total=Sum('amount'))['total'] or 0
    avg_amount = spends.aggregate(avg=Avg('amount'))['avg'] or 0
    
    # Get spending by type
    daily_spends = spends.filter(spend_type=SpendType.DAILY)
    monthly_spends = spends.filter(spend_type=SpendType.MONTHLY)
    
    daily_amount = daily_spends.aggregate(total=Sum('amount'))['total'] or 0
    monthly_amount = monthly_spends.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get spending by date (last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    recent_spends = spends.filter(spend_date__gte=start_date)
    
    date_breakdown = recent_spends.values('spend_date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('spend_date')
    
    context = {
        'campaign': campaign,
        'spends': spends,
        'total_spends': total_spends,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'daily_amount': daily_amount,
        'monthly_amount': monthly_amount,
        'date_breakdown': date_breakdown,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'spending/campaign_detail.html', context)


def spending_stats_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for spending statistics."""
    # Get overall statistics
    total_spends = Spend.objects.count()
    total_amount = Spend.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get today's statistics
    today = date.today()
    today_spends = Spend.objects.filter(spend_date=today)
    today_amount = today_spends.aggregate(total=Sum('amount'))['total'] or 0
    today_count = today_spends.count()
    
    # Get this month's statistics
    current_month = today.month
    current_year = today.year
    month_spends = Spend.objects.filter(
        spend_date__year=current_year,
        spend_date__month=current_month
    )
    month_amount = month_spends.aggregate(total=Sum('amount'))['total'] or 0
    month_count = month_spends.count()
    
    # Get spending by type
    daily_amount = Spend.objects.filter(spend_type=SpendType.DAILY).aggregate(
        total=Sum('amount')
    )['total'] or 0
    monthly_amount = Spend.objects.filter(spend_type=SpendType.MONTHLY).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    stats = {
        'total_spends': total_spends,
        'total_amount': float(total_amount),
        'today_amount': float(today_amount),
        'today_count': today_count,
        'month_amount': float(month_amount),
        'month_count': month_count,
        'daily_amount': float(daily_amount),
        'monthly_amount': float(monthly_amount),
        'date': today.isoformat(),
    }
    
    return JsonResponse(stats)

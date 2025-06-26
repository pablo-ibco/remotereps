"""
Views for brands app.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from .models import Brand


def brand_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view for brands overview."""
    brands = Brand.objects.all().prefetch_related('campaigns')
    
    # Calculate summary statistics
    total_brands = brands.count()
    total_campaigns = sum(brand.get_total_campaigns() for brand in brands)
    total_daily_spend = sum(brand.get_total_daily_spend() for brand in brands)
    total_monthly_spend = sum(brand.get_total_monthly_spend() for brand in brands)
    
    context = {
        'brands': brands,
        'total_brands': total_brands,
        'total_campaigns': total_campaigns,
        'total_daily_spend': total_daily_spend,
        'total_monthly_spend': total_monthly_spend,
    }
    
    return render(request, 'brands/dashboard.html', context)


def brand_detail(request: HttpRequest, brand_id: str) -> HttpResponse:
    """Detail view for a specific brand."""
    brand = get_object_or_404(Brand, id=brand_id)
    campaigns = brand.campaigns.all()
    
    context = {
        'brand': brand,
        'campaigns': campaigns,
        'total_campaigns': brand.get_total_campaigns(),
        'total_daily_spend': brand.get_total_daily_spend(),
        'total_monthly_spend': brand.get_total_monthly_spend(),
        'remaining_daily_budget': brand.get_remaining_daily_budget(),
        'remaining_monthly_budget': brand.get_remaining_monthly_budget(),
        'is_over_daily_budget': brand.is_over_daily_budget(),
        'is_over_monthly_budget': brand.is_over_monthly_budget(),
    }
    
    return render(request, 'brands/detail.html', context)


def brand_stats_api(request: HttpRequest, brand_id: str) -> JsonResponse:
    """API endpoint for brand statistics."""
    brand = get_object_or_404(Brand, id=brand_id)
    
    stats = {
        'id': str(brand.id),
        'name': brand.name,
        'daily_budget': float(brand.daily_budget),
        'monthly_budget': float(brand.monthly_budget),
        'total_campaigns': brand.get_total_campaigns(),
        'total_daily_spend': float(brand.get_total_daily_spend()),
        'total_monthly_spend': float(brand.get_total_monthly_spend()),
        'remaining_daily_budget': float(brand.get_remaining_daily_budget()),
        'remaining_monthly_budget': float(brand.get_remaining_monthly_budget()),
        'is_over_daily_budget': brand.is_over_daily_budget(),
        'is_over_monthly_budget': brand.is_over_monthly_budget(),
        'daily_budget_percentage': float((brand.get_total_daily_spend() / brand.daily_budget) * 100),
        'monthly_budget_percentage': float((brand.get_total_monthly_spend() / brand.monthly_budget) * 100),
    }
    
    return JsonResponse(stats)

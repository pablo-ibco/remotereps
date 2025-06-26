"""
Views for scheduling app.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest
from .models import Schedule, DayOfWeek
from .services import SchedulingService
from campaigns.models import Campaign, CampaignStatus
from django.utils import timezone
from typing import Dict, Any, List


def scheduling_dashboard(request: HttpRequest) -> Any:
    """Dashboard view for scheduling overview."""
    service = SchedulingService()
    
    # Get all campaigns
    campaigns = Campaign.objects.all().select_related('brand')
    
    # Get scheduling statistics
    total_campaigns = campaigns.count()
    campaigns_with_schedules = campaigns.filter(schedules__isnull=False).distinct().count()
    campaigns_without_schedules = total_campaigns - campaigns_with_schedules
    
    # Get campaigns that should be active/paused now
    campaigns_that_should_be_active = service.get_campaigns_that_should_be_active()
    campaigns_that_should_be_paused = service.get_campaigns_that_should_be_paused()
    
    # Get all schedules
    schedules = Schedule.objects.all().select_related('campaign__brand')
    total_schedules = schedules.count()
    active_schedules = schedules.filter(is_active=True).count()
    inactive_schedules = total_schedules - active_schedules
    
    # Get schedules by day of week
    schedules_by_day: Dict[str, int] = {}
    for day_num in range(7):
        day_name = DayOfWeek(day_num).label
        count = schedules.filter(day_of_week=day_num, is_active=True).count()
        schedules_by_day[day_name] = count
    
    context = {
        'total_campaigns': total_campaigns,
        'campaigns_with_schedules': campaigns_with_schedules,
        'campaigns_without_schedules': campaigns_without_schedules,
        'campaigns_that_should_be_active': campaigns_that_should_be_active,
        'campaigns_that_should_be_paused': campaigns_that_should_be_paused,
        'total_schedules': total_schedules,
        'active_schedules': active_schedules,
        'inactive_schedules': inactive_schedules,
        'schedules_by_day': schedules_by_day,
        'campaigns': campaigns,
    }
    
    return render(request, 'scheduling/dashboard.html', context)


def campaign_schedules(request: HttpRequest, campaign_id: str) -> Any:
    """View for managing campaign schedules."""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    service = SchedulingService()
    
    # Get all schedules for this campaign
    schedules = campaign.schedules.all().order_by('day_of_week', 'start_time')
    
    # Get schedule summary
    schedule_summary = service.get_campaign_schedule_summary(campaign)
    
    # Check if campaign is scheduled now
    is_scheduled_now = service.is_campaign_scheduled_now(campaign)
    
    # Get day of week choices for form
    day_choices = DayOfWeek.choices
    
    context = {
        'campaign': campaign,
        'schedules': schedules,
        'schedule_summary': schedule_summary,
        'is_scheduled_now': is_scheduled_now,
        'day_choices': day_choices,
        'total_schedules': schedules.count(),
        'active_schedules': schedules.filter(is_active=True).count(),
    }
    
    return render(request, 'scheduling/campaign_schedules.html', context)


def schedule_detail(request: HttpRequest, schedule_id: str) -> Any:
    """Detail view for a specific schedule."""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Get other schedules for the same campaign
    other_schedules = schedule.campaign.schedules.exclude(id=schedule.id).order_by('day_of_week', 'start_time')
    
    context = {
        'schedule': schedule,
        'other_schedules': other_schedules,
        'day_name': schedule.get_day_of_week_display(),
        'time_range': f"{schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}",
    }
    
    return render(request, 'scheduling/schedule_detail.html', context)


def dayparting_status(request: HttpRequest) -> Any:
    """View showing current dayparting status."""
    service = SchedulingService()
    
    # Get current time information
    now = timezone.now()
    current_day = now.weekday()
    current_time = now.time()
    current_day_name = DayOfWeek(current_day).label
    
    # Get campaigns that should be active/paused
    campaigns_that_should_be_active = service.get_campaigns_that_should_be_active()
    campaigns_that_should_be_paused = service.get_campaigns_that_should_be_paused()
    
    # Get all active schedules for today
    today_schedules = Schedule.objects.filter(
        day_of_week=current_day,
        is_active=True
    ).select_related('campaign__brand').order_by('start_time')
    
    # Check which schedules are currently active
    active_schedules: List[Schedule] = []
    inactive_schedules: List[Schedule] = []
    
    for schedule in today_schedules:
        if schedule.is_time_in_range(current_time):
            active_schedules.append(schedule)
        else:
            inactive_schedules.append(schedule)
    
    context = {
        'current_day': current_day_name,
        'current_time': current_time.strftime('%H:%M:%S'),
        'current_date': now.date(),
        'campaigns_that_should_be_active': campaigns_that_should_be_active,
        'campaigns_that_should_be_paused': campaigns_that_should_be_paused,
        'today_schedules': today_schedules,
        'active_schedules': active_schedules,
        'inactive_schedules': inactive_schedules,
        'total_active_schedules': len(active_schedules),
        'total_inactive_schedules': len(inactive_schedules),
    }
    
    return render(request, 'scheduling/dayparting_status.html', context)


def scheduling_stats_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for scheduling statistics."""
    service = SchedulingService()
    
    # Get basic statistics
    total_campaigns = Campaign.objects.count()
    campaigns_with_schedules = Campaign.objects.filter(schedules__isnull=False).distinct().count()
    campaigns_without_schedules = total_campaigns - campaigns_with_schedules
    
    # Get schedule statistics
    total_schedules = Schedule.objects.count()
    active_schedules = Schedule.objects.filter(is_active=True).count()
    inactive_schedules = total_schedules - active_schedules
    
    # Get current dayparting status
    campaigns_that_should_be_active = len(service.get_campaigns_that_should_be_active())
    campaigns_that_should_be_paused = len(service.get_campaigns_that_should_be_paused())
    
    # Get current time info
    now = timezone.now()
    current_day = now.weekday()
    current_time = now.time()
    
    stats = {
        'total_campaigns': total_campaigns,
        'campaigns_with_schedules': campaigns_with_schedules,
        'campaigns_without_schedules': campaigns_without_schedules,
        'total_schedules': total_schedules,
        'active_schedules': active_schedules,
        'inactive_schedules': inactive_schedules,
        'campaigns_that_should_be_active': campaigns_that_should_be_active,
        'campaigns_that_should_be_paused': campaigns_that_should_be_paused,
        'current_day': DayOfWeek(current_day).label,
        'current_time': current_time.strftime('%H:%M:%S'),
        'current_date': now.date().isoformat(),
    }
    
    return JsonResponse(stats)

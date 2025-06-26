"""
Scheduling services for budget management system.
"""

import logging
from typing import List, Optional
from django.utils import timezone
from campaigns.models import Campaign, CampaignStatus, PauseReason
from .models import Schedule

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Service for managing campaign scheduling and dayparting.
    
    This service handles the logic for determining when campaigns
    should be active based on their dayparting schedules.
    """
    
    def __init__(self) -> None:
        """Initialize the scheduling service."""
        pass
    
    def is_campaign_scheduled_now(self, campaign: Campaign) -> bool:
        """
        Check if a campaign should be active right now based on its schedules.
        
        Args:
            campaign: The campaign to check
            
        Returns:
            True if the campaign should be active, False otherwise
        """
        now = timezone.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()
        
        schedule = Schedule.get_schedule_for_campaign_and_day(campaign, current_day)
        
        if not schedule:
            return False
        
        return schedule.is_time_in_range(current_time)
    
    def get_campaigns_that_should_be_active(self) -> List[Campaign]:
        """
        Get all campaigns that should be active right now based on their schedules.
        
        Returns:
            List of campaigns that should be active
        """
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()
        
        # Get all active schedules for today
        schedules = Schedule.objects.filter(
            day_of_week=current_day,
            is_active=True,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).select_related('campaign')
        
        return [schedule.campaign for schedule in schedules]
    
    def get_campaigns_that_should_be_paused(self) -> List[Campaign]:
        """
        Get all campaigns that should be paused right now based on their schedules.
        
        Returns:
            List of campaigns that should be paused
        """
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()
        
        # Get all campaigns that are currently active
        active_campaigns = Campaign.objects.filter(status=CampaignStatus.ACTIVE)
        
        campaigns_to_pause = []
        
        for campaign in active_campaigns:
            schedule = Schedule.get_schedule_for_campaign_and_day(campaign, current_day)
            
            if not schedule:
                # No schedule for today, should be paused
                campaigns_to_pause.append(campaign)
            elif not schedule.is_time_in_range(current_time):
                # Outside scheduled time, should be paused
                campaigns_to_pause.append(campaign)
        
        return campaigns_to_pause
    
    def enforce_dayparting(self) -> dict:
        """
        Enforce dayparting rules for all campaigns.
        
        This method checks all campaigns and ensures they are in the correct
        state based on their dayparting schedules.
        
        Returns:
            Dictionary with results of the enforcement
        """
        logger.info("Starting dayparting enforcement")
        
        results = {
            'activated': 0,
            'paused': 0,
            'errors': 0
        }
        
        try:
            # Pause campaigns that should be paused
            campaigns_to_pause = self.get_campaigns_that_should_be_paused()
            
            for campaign in campaigns_to_pause:
                try:
                    if campaign.is_active():
                        campaign.pause(PauseReason.OUTSIDE_SCHEDULE)
                        results['paused'] += 1
                        logger.info(f"Paused campaign {campaign.id} due to dayparting")
                except Exception as e:
                    logger.error(f"Error pausing campaign {campaign.id}: {e}")
                    results['errors'] += 1
            
            # Activate campaigns that should be active
            campaigns_that_should_be_active = self.get_campaigns_that_should_be_active()
            
            for campaign in campaigns_that_should_be_active:
                try:
                    if campaign.is_paused() and campaign.pause_reason in [
                        PauseReason.OUTSIDE_SCHEDULE,
                        PauseReason.NO_SCHEDULE
                    ]:
                        if campaign.can_be_activated():
                            campaign.activate()
                            results['activated'] += 1
                            logger.info(f"Activated campaign {campaign.id} due to dayparting")
                except Exception as e:
                    logger.error(f"Error activating campaign {campaign.id}: {e}")
                    results['errors'] += 1
            
            logger.info(f"Dayparting enforcement completed: {results}")
            
        except Exception as e:
            logger.error(f"Error during dayparting enforcement: {e}")
            results['errors'] += 1
        
        return results
    
    def create_default_schedule(self, campaign: Campaign) -> Schedule:
        """
        Create a default 24/7 schedule for a campaign.
        
        Args:
            campaign: The campaign to create a schedule for
            
        Returns:
            The created schedule
        """
        from datetime import time
        
        # Create schedules for all days of the week (24/7)
        schedules = []
        
        for day in range(7):  # 0=Monday to 6=Sunday
            schedule = Schedule.objects.create(
                campaign=campaign,
                day_of_week=day,
                start_time=time(0, 0),  # 00:00
                end_time=time(23, 59, 59),  # 23:59:59
                is_active=True
            )
            schedules.append(schedule)
        
        logger.info(f"Created default 24/7 schedule for campaign {campaign.id}")
        return schedules[0]  # Return first schedule for convenience
    
    def get_campaign_schedule_summary(self, campaign: Campaign) -> dict:
        """
        Get a summary of a campaign's scheduling configuration.
        
        Args:
            campaign: The campaign to get schedule summary for
            
        Returns:
            Dictionary with schedule summary
        """
        schedules = Schedule.get_active_schedules_for_campaign(campaign)
        
        summary = {
            'campaign_id': str(campaign.id),
            'campaign_name': campaign.name,
            'total_schedules': len(schedules),
            'schedules_by_day': {},
            'is_scheduled_now': self.is_campaign_scheduled_now(campaign)
        }
        
        for schedule in schedules:
            day_name = schedule.get_day_of_week_display()
            summary['schedules_by_day'][day_name] = {
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'is_active': schedule.is_active
            }
        
        return summary 
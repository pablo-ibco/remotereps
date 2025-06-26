"""
Scheduling models for budget management system.
"""

from __future__ import annotations
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import Optional, List, Any
import uuid
from campaigns.models import Campaign
from datetime import time


class DayOfWeek(models.IntegerChoices):
    """Day of week choices (0=Monday, 6=Sunday)."""
    MONDAY = 0, 'Monday'
    TUESDAY = 1, 'Tuesday'
    WEDNESDAY = 2, 'Wednesday'
    THURSDAY = 3, 'Thursday'
    FRIDAY = 4, 'Friday'
    SATURDAY = 5, 'Saturday'
    SUNDAY = 6, 'Sunday'


class Schedule(models.Model):
    """
    Schedule model representing dayparting configuration.
    
    Each schedule defines when a campaign should be active
    on specific days of the week and time ranges.
    """
    
    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    campaign: models.ForeignKey = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Campaign this schedule is for"
    )
    
    day_of_week: models.IntegerField = models.IntegerField(
        choices=DayOfWeek.choices,
        help_text="Day of the week"
    )
    
    start_time: models.TimeField = models.TimeField(
        help_text="Start time for the schedule"
    )
    
    end_time: models.TimeField = models.TimeField(
        help_text="End time for the schedule"
    )
    
    is_active: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Is this schedule active?"
    )
    
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedules'
        ordering = ['campaign__name', 'day_of_week', 'start_time']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        unique_together = ['campaign', 'day_of_week', 'start_time', 'end_time']
    
    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def clean(self) -> None:
        """Validate that end_time is after start_time."""
        from django.core.exceptions import ValidationError
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to validate time range."""
        self.clean()
        super().save(*args, **kwargs)
    
    def is_time_in_range(self, check_time: time) -> bool:
        """Check if a given time falls within this schedule's range."""
        return bool(self.start_time <= check_time <= self.end_time)
    
    @classmethod
    def get_active_schedules_for_campaign(cls, campaign: Campaign) -> List['Schedule']:
        """Get all active schedules for a campaign."""
        return list(cls.objects.filter(
            campaign=campaign,
            is_active=True
        ).order_by('day_of_week', 'start_time'))
    
    @classmethod
    def get_schedule_for_campaign_and_day(cls, campaign: Campaign, day_of_week: int) -> Optional['Schedule']:
        """Get schedule for a campaign on a specific day."""
        try:
            return cls.objects.get(campaign=campaign, day_of_week=day_of_week, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def is_campaign_scheduled_now(cls, campaign: Campaign) -> bool:
        """Check if a campaign should be active right now based on its schedules."""
        from django.utils import timezone
        
        now = timezone.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()
        
        schedule = cls.get_schedule_for_campaign_and_day(campaign, current_day)
        
        if not schedule:
            return False
        
        return schedule.is_time_in_range(current_time)

"""
Campaign models for budget management system.
"""

from __future__ import annotations
from typing import Any, Optional, List
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
import uuid
from brands.models import Brand
from django.db.models import F
from django.utils import timezone


class CampaignStatus(models.TextChoices):
    """Campaign status choices."""
    ACTIVE = 'ACTIVE', 'Active'
    PAUSED = 'PAUSED', 'Paused'


class PauseReason(models.TextChoices):
    """Campaign pause reason choices."""
    DAILY_BUDGET_EXCEEDED = 'DAILY_BUDGET_EXCEEDED', 'Daily Budget Exceeded'
    MONTHLY_BUDGET_EXCEEDED = 'MONTHLY_BUDGET_EXCEEDED', 'Monthly Budget Exceeded'
    OUTSIDE_SCHEDULE = 'OUTSIDE_SCHEDULE', 'Outside Schedule'
    NO_SCHEDULE = 'NO_SCHEDULE', 'No Schedule'
    MANUAL = 'MANUAL', 'Manual Pause'


class Campaign(models.Model):
    """
    Campaign model representing an advertising campaign.
    
    Each campaign belongs to a brand and tracks its own spending.
    Campaigns can be paused automatically based on budget limits
    or dayparting schedules.
    """
    
    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    brand: models.ForeignKey = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='campaigns',
        help_text="Brand that owns this campaign"
    )
    
    name: models.CharField = models.CharField(
        max_length=255,
        help_text="Campaign name"
    )
    
    status: models.CharField = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.ACTIVE,
        help_text="Current campaign status"
    )
    
    daily_spend: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total spend for current day"
    )
    
    monthly_spend: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total spend for current month"
    )
    
    pause_reason: models.CharField = models.CharField(
        max_length=50,
        choices=PauseReason.choices,
        null=True,
        blank=True,
        help_text="Reason why campaign was paused"
    )
    
    paused_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the campaign was paused"
    )
    
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaigns'
        ordering = ['brand__name', 'name']
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        unique_together = ['brand', 'name']
    
    def __str__(self) -> str:
        return f"{self.brand.name} - {self.name}"
    
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        return bool(self.status == CampaignStatus.ACTIVE)
    
    def is_paused(self) -> bool:
        """Check if campaign is currently paused."""
        return bool(self.status == CampaignStatus.PAUSED)
    
    def pause(self, reason: str) -> None:
        """Pause the campaign with a specific reason."""
        from django.utils import timezone
        
        self.status = CampaignStatus.PAUSED
        self.pause_reason = reason
        self.paused_at = timezone.now()
        self.save(update_fields=['status', 'pause_reason', 'paused_at', 'updated_at'])
    
    def activate(self) -> bool:
        """Activate the campaign if possible."""
        from scheduling.services import SchedulingService
        
        # Check if campaign can be activated
        if not self.can_be_activated():
            return False
        
        self.status = CampaignStatus.ACTIVE
        self.pause_reason = None
        self.paused_at = None
        self.save(update_fields=['status', 'pause_reason', 'paused_at', 'updated_at'])
        return True
    
    def can_be_activated(self) -> bool:
        """Check if campaign can be activated based on budget and schedule."""
        from scheduling.services import SchedulingService
        
        # Check budget limits
        if self.daily_spend >= self.brand.daily_budget:
            return False
        
        if self.monthly_spend >= self.brand.monthly_budget:
            return False
        
        # Check dayparting schedule
        scheduling_service = SchedulingService()
        if not scheduling_service.is_campaign_scheduled_now(self):
            return False
        
        return True
    
    def add_spend(self, amount: Decimal) -> None:
        """Add spend to the campaign and update totals."""
        from decimal import Decimal
        from django.utils import timezone
        if amount <= Decimal('0.00'):
            raise ValueError("Spend amount must be positive")
        
        # Update the instance directly
        self.daily_spend += amount
        self.monthly_spend += amount
        self.updated_at = timezone.now()
        self.save(update_fields=['daily_spend', 'monthly_spend', 'updated_at'])
    
    def reset_daily_spend(self) -> None:
        """Reset daily spend to zero."""
        self.daily_spend = Decimal('0.00')
        self.save(update_fields=['daily_spend', 'updated_at'])
    
    def reset_monthly_spend(self) -> None:
        """Reset monthly spend to zero."""
        self.monthly_spend = Decimal('0.00')
        self.save(update_fields=['monthly_spend', 'updated_at'])
    
    def get_daily_spend(self) -> Decimal:
        return Decimal(self.daily_spend)

    def get_monthly_spend(self) -> Decimal:
        return Decimal(self.monthly_spend)

    def get_remaining_daily_budget(self) -> Decimal:
        return Decimal(self.brand.daily_budget) - Decimal(self.daily_spend)

    def get_remaining_monthly_budget(self) -> Decimal:
        return Decimal(self.brand.monthly_budget) - Decimal(self.monthly_spend)

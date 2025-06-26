"""
Spending models for budget management system.
"""

from __future__ import annotations
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from typing import Optional, List, Any
import uuid
from campaigns.models import Campaign
from datetime import date


class SpendType(models.TextChoices):
    """Spend type choices."""
    DAILY = 'DAILY', 'Daily'
    MONTHLY = 'MONTHLY', 'Monthly'


class Spend(models.Model):
    """
    Spend model representing individual spending records.
    
    Each spend record tracks a specific amount spent by a campaign
    on a specific date. This provides an audit trail and allows for
    detailed reporting and analysis.
    """
    
    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    campaign: models.ForeignKey = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='spends',
        help_text="Campaign this spend is related to"
    )
    
    amount: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount spent"
    )
    
    spend_date: models.DateField = models.DateField(
        help_text="Date of the spend"
    )
    
    spend_type: models.CharField = models.CharField(
        max_length=10,
        choices=SpendType.choices,
        default=SpendType.DAILY,
        help_text="Type of spend (daily/monthly)"
    )
    
    description: models.CharField = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Description of the spend"
    )
    
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'spends'
        ordering = ['-spend_date', '-created_at']
        verbose_name = 'Spend'
        verbose_name_plural = 'Spends'
        indexes = [
            models.Index(fields=['campaign', 'spend_date']),
            models.Index(fields=['spend_date']),
            models.Index(fields=['spend_type']),
        ]
    
    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.amount} on {self.spend_date}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to update campaign totals."""
        is_new = self.pk is None
        
        # Save the spend record
        super().save(*args, **kwargs)
        
        # Update campaign totals if this is a new record
        if is_new:
            self.campaign.add_spend(self.amount)
    
    @classmethod
    def get_daily_spend_for_campaign(cls, campaign: Campaign, date: date) -> Decimal:
        """Get total daily spend for a campaign on a specific date."""
        total = cls.objects.filter(
            campaign=campaign,
            spend_date=date,
            spend_type=SpendType.DAILY
        ).aggregate(
            total=models.Sum('amount')
        )['total']
        
        return total or Decimal('0.00')
    
    @classmethod
    def get_monthly_spend_for_campaign(cls, campaign: Campaign, year: int, month: int) -> Decimal:
        """Get total monthly spend for a campaign in a specific month."""
        from django.db.models import Q
        
        total = cls.objects.filter(
            campaign=campaign,
            spend_date__year=year,
            spend_date__month=month,
            spend_type=SpendType.MONTHLY
        ).aggregate(
            total=models.Sum('amount')
        )['total']
        
        return total or Decimal('0.00')
    
    @classmethod
    def get_daily_spend_for_brand(cls, brand_id: uuid.UUID) -> Decimal:
        from campaigns.models import Campaign
        campaigns = Campaign.objects.filter(brand_id=brand_id)
        return sum((Decimal(c.daily_spend) for c in campaigns), Decimal('0.00'))
    
    @classmethod
    def get_monthly_spend_for_brand(cls, brand_id: uuid.UUID) -> Decimal:
        from campaigns.models import Campaign
        campaigns = Campaign.objects.filter(brand_id=brand_id)
        return sum((Decimal(c.monthly_spend) for c in campaigns), Decimal('0.00'))

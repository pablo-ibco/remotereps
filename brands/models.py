"""
Brand models for budget management system.
"""

from __future__ import annotations
from typing import Any, Optional
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from typing import List
import uuid


class Brand(models.Model):
    """
    Brand model representing a client/advertiser.
    
    Each brand has daily and monthly budgets that control
    the spending limits for all its campaigns.
    """
    
    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name: models.CharField = models.CharField(
        max_length=255,
        unique=True,
        help_text="Brand name"
    )
    
    daily_budget: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Daily budget for the brand"
    )
    
    monthly_budget: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly budget for the brand"
    )
    
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'brands'
        ordering = ['name']
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        unique_together = ['name']
    
    def __str__(self) -> str:
        return str(self.name)
    
    def get_daily_budget(self) -> Decimal:
        return Decimal(str(self.daily_budget))
    
    def get_monthly_budget(self) -> Decimal:
        return Decimal(str(self.monthly_budget))
    
    def get_total_campaigns(self) -> int:
        return self.campaigns.count() if hasattr(self, 'campaigns') else 0
    
    def get_total_daily_spend(self) -> Decimal:
        try:
            return sum((Decimal(str(c.daily_spend)) for c in self.campaigns.all()), Decimal('0.00'))
        except Exception:
            return Decimal('0.00')
    
    def get_total_monthly_spend(self) -> Decimal:
        try:
            return sum((Decimal(str(c.monthly_spend)) for c in self.campaigns.all()), Decimal('0.00'))
        except Exception:
            return Decimal('0.00')
    
    def get_remaining_daily_budget(self) -> Decimal:
        return Decimal(str(self.daily_budget)) - self.get_total_daily_spend()
    
    def get_remaining_monthly_budget(self) -> Decimal:
        return Decimal(str(self.monthly_budget)) - self.get_total_monthly_spend()
    
    def is_over_daily_budget(self) -> bool:
        return bool(self.get_total_daily_spend() >= Decimal(str(self.daily_budget)))
    
    def is_over_monthly_budget(self) -> bool:
        return bool(self.get_total_monthly_spend() >= Decimal(str(self.monthly_budget)))

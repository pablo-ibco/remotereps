"""
Spending services for budget management system.
"""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import date
from campaigns.models import Campaign, CampaignStatus, PauseReason
from .models import Spend, SpendType

logger = logging.getLogger(__name__)


class SpendingService:
    """
    Service for managing campaign spending and budget enforcement.
    
    This service handles the logic for tracking spend, checking budget limits,
    and enforcing budget constraints on campaigns.
    """
    
    def __init__(self) -> None:
        """Initialize the spending service."""
        pass
    
    def track_spend(
        self, 
        campaign: Campaign, 
        amount: Decimal, 
        spend_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Spend:
        """
        Track a new spend for a campaign.
        
        Args:
            campaign: The campaign to track spend for
            amount: The amount spent
            spend_date: The date of the spend (defaults to today)
            description: Optional description of the spend
            
        Returns:
            The created spend record
            
        Raises:
            ValueError: If amount is not positive
        """
        if amount <= Decimal('0.00'):
            raise ValueError("Spend amount must be positive")
        
        if spend_date is None:
            spend_date = timezone.now().date()
        
        with transaction.atomic():
            # Create the spend record
            spend = Spend.objects.create(
                campaign=campaign,
                amount=amount,
                spend_date=spend_date,
                spend_type=SpendType.DAILY,
                description=description
            )
            
            # Check budget limits after adding spend
            self.check_budget_limits(campaign)
            
            logger.info(f"Tracked spend of {amount} for campaign {campaign.id}")
            
            return spend
    
    def check_budget_limits(self, campaign: Campaign) -> Dict[str, Any]:
        """
        Check if a campaign has exceeded its budget limits.
        
        Args:
            campaign: The campaign to check
            
        Returns:
            Dictionary with budget check results
        """
        results: Dict[str, Any] = {
            'daily_exceeded': False,
            'monthly_exceeded': False,
            'action_taken': None
        }
        
        # Check daily budget
        if campaign.daily_spend >= campaign.brand.daily_budget:
            results['daily_exceeded'] = True
            if campaign.is_active():
                campaign.pause(PauseReason.DAILY_BUDGET_EXCEEDED)
                results['action_taken'] = 'paused_daily'
                logger.info(f"Paused campaign {campaign.id} due to daily budget limit")
        
        # Check monthly budget
        if campaign.monthly_spend >= campaign.brand.monthly_budget:
            results['monthly_exceeded'] = True
            if campaign.is_active():
                campaign.pause(PauseReason.MONTHLY_BUDGET_EXCEEDED)
                results['action_taken'] = 'paused_monthly'
                logger.info(f"Paused campaign {campaign.id} due to monthly budget limit")
        
        return results
    
    def enforce_budget_limits(self) -> Dict[str, int]:
        """
        Enforce budget limits for all active campaigns.
        
        Returns:
            Dictionary with enforcement results
        """
        logger.info("Starting budget enforcement")
        
        results = {
            'checked': 0,
            'paused_daily': 0,
            'paused_monthly': 0,
            'errors': 0
        }
        
        try:
            # Get all active campaigns
            active_campaigns = Campaign.objects.filter(status=CampaignStatus.ACTIVE)
            
            for campaign in active_campaigns:
                try:
                    results['checked'] += 1
                    budget_check = self.check_budget_limits(campaign)
                    
                    if budget_check['action_taken'] == 'paused_daily':
                        results['paused_daily'] += 1
                    elif budget_check['action_taken'] == 'paused_monthly':
                        results['paused_monthly'] += 1
                        
                except Exception as e:
                    logger.error(f"Error checking budget for campaign {campaign.id}: {e}")
                    results['errors'] += 1
            
            logger.info(f"Budget enforcement completed: {results}")
            
        except Exception as e:
            logger.error(f"Error during budget enforcement: {e}")
            results['errors'] += 1
        
        return results
    
    def reset_daily_spends(self) -> Dict[str, int]:
        """
        Reset daily spends for all campaigns and reactivate eligible ones.
        
        Returns:
            Dictionary with reset results
        """
        logger.info("Starting daily spend reset")
        
        results = {
            'reset': 0,
            'reactivated': 0,
            'errors': 0
        }
        
        try:
            with transaction.atomic():
                # Reset daily spends for all campaigns
                campaigns = Campaign.objects.all()
                
                for campaign in campaigns:
                    try:
                        campaign.reset_daily_spend()
                        results['reset'] += 1
                    except Exception as e:
                        logger.error(f"Error resetting daily spend for campaign {campaign.id}: {e}")
                        results['errors'] += 1
                
                # Reactivate campaigns that were paused due to daily budget
                paused_campaigns = Campaign.objects.filter(
                    status=CampaignStatus.PAUSED,
                    pause_reason=PauseReason.DAILY_BUDGET_EXCEEDED
                )
                
                for campaign in paused_campaigns:
                    try:
                        if campaign.can_be_activated():
                            campaign.activate()
                            results['reactivated'] += 1
                            logger.info(f"Reactivated campaign {campaign.id} after daily reset")
                    except Exception as e:
                        logger.error(f"Error reactivating campaign {campaign.id}: {e}")
                        results['errors'] += 1
            
            logger.info(f"Daily spend reset completed: {results}")
            
        except Exception as e:
            logger.error(f"Error during daily spend reset: {e}")
            results['errors'] += 1
        
        return results
    
    def reset_monthly_spends(self) -> Dict[str, int]:
        """
        Reset monthly spends for all campaigns and reactivate eligible ones.
        
        Returns:
            Dictionary with reset results
        """
        logger.info("Starting monthly spend reset")
        
        results = {
            'reset': 0,
            'reactivated': 0,
            'errors': 0
        }
        
        try:
            with transaction.atomic():
                # Reset monthly spends for all campaigns
                campaigns = Campaign.objects.all()
                
                for campaign in campaigns:
                    try:
                        campaign.reset_monthly_spend()
                        results['reset'] += 1
                    except Exception as e:
                        logger.error(f"Error resetting monthly spend for campaign {campaign.id}: {e}")
                        results['errors'] += 1
                
                # Reactivate campaigns that were paused due to monthly budget
                paused_campaigns = Campaign.objects.filter(
                    status=CampaignStatus.PAUSED,
                    pause_reason=PauseReason.MONTHLY_BUDGET_EXCEEDED
                )
                
                for campaign in paused_campaigns:
                    try:
                        if campaign.can_be_activated():
                            campaign.activate()
                            results['reactivated'] += 1
                            logger.info(f"Reactivated campaign {campaign.id} after monthly reset")
                    except Exception as e:
                        logger.error(f"Error reactivating campaign {campaign.id}: {e}")
                        results['errors'] += 1
            
            logger.info(f"Monthly spend reset completed: {results}")
            
        except Exception as e:
            logger.error(f"Error during monthly spend reset: {e}")
            results['errors'] += 1
        
        return results
    
    def get_spending_summary(self, campaign: Campaign) -> Dict[str, Any]:
        """
        Get a summary of spending for a campaign.
        
        Args:
            campaign: The campaign to get summary for
            
        Returns:
            Dictionary with spending summary
        """
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        daily_spend = Spend.get_daily_spend_for_campaign(campaign, today)
        monthly_spend = Spend.get_monthly_spend_for_campaign(campaign, current_year, current_month)
        
        summary = {
            'campaign_id': str(campaign.id),
            'campaign_name': campaign.name,
            'brand_name': campaign.brand.name,
            'daily_spend': float(daily_spend),
            'monthly_spend': float(monthly_spend),
            'daily_budget': float(campaign.brand.daily_budget),
            'monthly_budget': float(campaign.brand.monthly_budget),
            'daily_remaining': float(campaign.get_remaining_daily_budget()),
            'monthly_remaining': float(campaign.get_remaining_monthly_budget()),
            'daily_percentage': float((daily_spend / campaign.brand.daily_budget) * 100),
            'monthly_percentage': float((monthly_spend / campaign.brand.monthly_budget) * 100),
            'status': campaign.status,
            'pause_reason': campaign.pause_reason
        }
        
        return summary
    
    def get_brand_spending_summary(self, brand_id: str) -> Dict[str, Any]:
        """
        Get a summary of spending for a brand.
        
        Args:
            brand_id: The brand ID to get summary for
            
        Returns:
            Dictionary with brand spending summary
        """
        from brands.models import Brand
        
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            raise ValueError(f"Brand with ID {brand_id} does not exist")
        
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        daily_spend = Spend.get_daily_spend_for_brand(brand.id)
        monthly_spend = Spend.get_monthly_spend_for_brand(brand.id)
        
        campaigns = brand.campaigns.all()
        
        summary = {
            'brand_id': str(brand.id),
            'brand_name': brand.name,
            'total_daily_spend': float(daily_spend),
            'total_monthly_spend': float(monthly_spend),
            'daily_budget': float(brand.daily_budget),
            'monthly_budget': float(brand.monthly_budget),
            'daily_remaining': float(brand.get_remaining_daily_budget()),
            'monthly_remaining': float(brand.get_remaining_monthly_budget()),
            'daily_percentage': float((daily_spend / brand.daily_budget) * 100),
            'monthly_percentage': float((monthly_spend / brand.monthly_budget) * 100),
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status=CampaignStatus.ACTIVE).count(),
            'paused_campaigns': campaigns.filter(status=CampaignStatus.PAUSED).count()
        }
        
        return summary 
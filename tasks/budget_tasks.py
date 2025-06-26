"""
Celery tasks for budget management system.
"""

import logging
from typing import Dict, Any, Optional
from celery import shared_task
from django.utils import timezone
from spending.services import SpendingService
from scheduling.services import SchedulingService

logger = logging.getLogger(__name__)


@shared_task(bind=True)  # type: ignore[misc]
def enforce_budget_limits_task(self: Any) -> Dict[str, int]:
    """
    Celery task to enforce budget limits for all active campaigns.
    
    This task runs every 5 minutes to check if any active campaigns
    have exceeded their daily or monthly budget limits and pauses them.
    
    Returns:
        Dictionary with enforcement results
    """
    logger.info("Starting budget enforcement task")
    
    try:
        spending_service = SpendingService()
        results = spending_service.enforce_budget_limits()
        
        logger.info(f"Budget enforcement task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in budget enforcement task: {e}")
        # Retry the task with exponential backoff
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)  # type: ignore[misc]
def enforce_dayparting_task(self: Any) -> Dict[str, int]:
    """
    Celery task to enforce dayparting rules for all campaigns.
    
    This task runs every minute to check if campaigns should be
    active or paused based on their dayparting schedules.
    
    Returns:
        Dictionary with dayparting enforcement results
    """
    logger.info("Starting dayparting enforcement task")
    
    try:
        scheduling_service = SchedulingService()
        results = scheduling_service.enforce_dayparting()
        
        logger.info(f"Dayparting enforcement task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in dayparting enforcement task: {e}")
        # Retry the task with exponential backoff
        raise self.retry(countdown=30, max_retries=3)


@shared_task(bind=True)  # type: ignore[misc]
def daily_reset_task(self: Any) -> Dict[str, int]:
    """
    Celery task to reset daily spends and reactivate eligible campaigns.
    
    This task runs daily at 00:00 to reset all daily spend counters
    and reactivate campaigns that were paused due to daily budget limits.
    
    Returns:
        Dictionary with daily reset results
    """
    logger.info("Starting daily reset task")
    
    try:
        spending_service = SpendingService()
        results = spending_service.reset_daily_spends()
        
        logger.info(f"Daily reset task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in daily reset task: {e}")
        # Retry the task with exponential backoff
        raise self.retry(countdown=300, max_retries=3)


@shared_task(bind=True)  # type: ignore[misc]
def monthly_reset_task(self: Any) -> Dict[str, int]:
    """
    Celery task to reset monthly spends and reactivate eligible campaigns.
    
    This task runs monthly on the 1st day at 00:00 to reset all monthly
    spend counters and reactivate campaigns that were paused due to
    monthly budget limits.
    
    Returns:
        Dictionary with monthly reset results
    """
    logger.info("Starting monthly reset task")
    
    try:
        spending_service = SpendingService()
        results = spending_service.reset_monthly_spends()
        
        logger.info(f"Monthly reset task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in monthly reset task: {e}")
        # Retry the task with exponential backoff
        raise self.retry(countdown=600, max_retries=3)


@shared_task(bind=True)  # type: ignore[misc]
def track_spend_task(self: Any, campaign_id: str, amount: float, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task to track a new spend for a campaign.
    
    Args:
        campaign_id: UUID of the campaign
        amount: Amount spent (as float, will be converted to Decimal)
        description: Optional description of the spend
        
    Returns:
        Dictionary with spend tracking results
    """
    logger.info(f"Starting spend tracking task for campaign {campaign_id}")
    
    try:
        from decimal import Decimal
        from campaigns.models import Campaign
        
        # Get the campaign
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            raise ValueError(f"Campaign with ID {campaign_id} does not exist")
        
        # Track the spend
        spending_service = SpendingService()
        spend = spending_service.track_spend(
            campaign=campaign,
            amount=Decimal(str(amount)),
            description=description
        )
        
        results = {
            'success': True,
            'spend_id': str(spend.id),
            'campaign_id': str(campaign.id),
            'amount': float(spend.amount),
            'spend_date': spend.spend_date.isoformat()
        }
        
        logger.info(f"Spend tracking task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in spend tracking task: {e}")
        results = {
            'success': False,
            'error': str(e),
            'campaign_id': campaign_id,
            'amount': amount
        }
        return results


@shared_task(bind=True)  # type: ignore[misc]
def health_check_task(self: Any) -> Dict[str, Any]:
    """
    Celery task to perform system health check.
    
    This task checks the overall health of the budget management system
    by verifying database connections, campaign states, and service availability.
    
    Returns:
        Dictionary with health check results
    """
    logger.info("Starting health check task")
    
    try:
        from campaigns.models import Campaign, CampaignStatus
        from brands.models import Brand
        from spending.models import Spend
        
        health_results: Dict[str, Any] = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        # Check database connectivity
        try:
            brand_count = Brand.objects.count()
            campaign_count = Campaign.objects.count()
            spend_count = Spend.objects.count()
            
            health_results['checks']['database'] = {
                'status': 'healthy',
                'brands': brand_count,
                'campaigns': campaign_count,
                'spends': spend_count
            }
        except Exception as e:
            health_results['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_results['status'] = 'unhealthy'
        
        # Check campaign states
        try:
            active_campaigns = Campaign.objects.filter(status=CampaignStatus.ACTIVE).count()
            paused_campaigns = Campaign.objects.filter(status=CampaignStatus.PAUSED).count()
            
            health_results['checks']['campaigns'] = {
                'status': 'healthy',
                'active': active_campaigns,
                'paused': paused_campaigns
            }
        except Exception as e:
            health_results['checks']['campaigns'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_results['status'] = 'unhealthy'
        
        # Check services
        try:
            spending_service = SpendingService()
            scheduling_service = SchedulingService()
            
            health_results['checks']['services'] = {
                'status': 'healthy',
                'spending_service': 'available',
                'scheduling_service': 'available'
            }
        except Exception as e:
            health_results['checks']['services'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_results['status'] = 'unhealthy'
        
        logger.info(f"Health check task completed: {health_results['status']}")
        return health_results
        
    except Exception as e:
        logger.error(f"Error in health check task: {e}")
        return {
            'timestamp': timezone.now().isoformat(),
            'status': 'unhealthy',
            'error': str(e)
        } 
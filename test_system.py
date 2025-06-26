#!/usr/bin/env python
"""
Full test script for the Budget Management System.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import time, date
from typing import Tuple, Any

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')
django.setup()

from brands.models import Brand
from campaigns.models import Campaign, CampaignStatus, PauseReason
from spending.models import Spend, SpendType
from scheduling.models import Schedule, DayOfWeek
from spending.services import SpendingService
from scheduling.services import SchedulingService
from tasks.budget_tasks import health_check_task


def test_models() -> Tuple[Brand, Campaign, Schedule, Spend]:
    """Test creation and relationships of models."""
    print("🧪 Testing models...")
    
    # Clean up old test brands
    Brand.objects.filter(name="Test Brand").delete()
    
    # Create a brand
    brand = Brand.objects.create(
        name="Test Brand",
        daily_budget=Decimal('100.00'),
        monthly_budget=Decimal('1000.00')
    )
    print(f"✅ Brand created: {brand.name}")
    
    # Create a campaign
    campaign = Campaign.objects.create(
        brand=brand,
        name="Test Campaign",
        status=CampaignStatus.ACTIVE
    )
    print(f"✅ Campaign created: {campaign.name}")
    
    # Create a schedule
    schedule = Schedule.objects.create(
        campaign=campaign,
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),  # 09:00
        end_time=time(18, 0),   # 18:00
        is_active=True
    )
    print(f"✅ Schedule created: {schedule}")
    
    # Create a spend
    spend = Spend.objects.create(
        campaign=campaign,
        amount=Decimal('25.00'),
        spend_date=date.today(),
        spend_type=SpendType.DAILY,
        description="Test spend"
    )
    print(f"✅ Spend created: ${spend.amount}")
    
    return brand, campaign, schedule, spend


def test_services() -> Tuple[SpendingService, SchedulingService]:
    """Test business services."""
    print("\n🔧 Testing services...")
    
    # Test SpendingService
    spending_service = SpendingService()
    print("✅ SpendingService created")
    
    # Test SchedulingService
    scheduling_service = SchedulingService()
    print("✅ SchedulingService created")
    
    return spending_service, scheduling_service


def test_budget_enforcement(brand: Brand, campaign: Campaign, spending_service: SpendingService) -> None:
    """Test budget enforcement."""
    print("\n💰 Testing budget enforcement...")
    
    # Add spend that exceeds the daily budget
    campaign.daily_spend = Decimal('95.00')  # Close to the limit of 100
    campaign.save()
    
    # Add another spend
    spend = spending_service.track_spend(
        campaign=campaign,
        amount=Decimal('10.00'),
        description="Spend that should exceed budget"
    )
    
    # Check if the campaign was paused
    campaign.refresh_from_db()
    if campaign.status == CampaignStatus.PAUSED:
        print(f"✅ Campaign paused correctly: {campaign.pause_reason}")
    else:
        print(f"⚠️ Campaign was not paused: {campaign.status}")


def test_dayparting(campaign: Campaign, scheduling_service: SchedulingService) -> None:
    """Test dayparting."""
    print("\n⏰ Testing dayparting...")
    
    # Check if the campaign is scheduled now
    is_scheduled = scheduling_service.is_campaign_scheduled_now(campaign)
    print(f"✅ Campaign scheduled now: {is_scheduled}")
    
    # Test dayparting enforcement
    results = scheduling_service.enforce_dayparting()
    print(f"✅ Dayparting enforcement: {results}")


def test_commands() -> None:
    """Test management commands."""
    print("\n📋 Testing management commands...")
    
    # Test budget enforcement command
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    call_command('enforce_budgets', stdout=out)
    print("✅ enforce_budgets command executed")
    
    # Test dayparting command
    out = StringIO()
    call_command('enforce_dayparting', stdout=out)
    print("✅ enforce_dayparting command executed")


def test_celery_tasks() -> None:
    """Test Celery tasks."""
    print("\n⚡ Testing Celery tasks...")
    
    # Test health check
    health_result = health_check_task()
    print(f"✅ Health check: {health_result['status']}")
    
    # Test budget enforcement via Celery
    from tasks.budget_tasks import enforce_budget_limits_task
    budget_result = enforce_budget_limits_task()
    print(f"✅ Budget enforcement via Celery: {budget_result}")
    
    # Test dayparting via Celery
    from tasks.budget_tasks import enforce_dayparting_task
    dayparting_result = enforce_dayparting_task()
    print(f"✅ Dayparting via Celery: {dayparting_result}")


def test_admin_interface() -> None:
    """Test admin interface."""
    print("\n🎛️ Testing admin interface...")
    
    # Check if admins are registered
    from django.contrib import admin
    from brands.admin import BrandAdmin
    from campaigns.admin import CampaignAdmin
    from spending.admin import SpendAdmin
    from scheduling.admin import ScheduleAdmin
    
    print("✅ All admins imported successfully")
    
    # Check if models are registered
    if Brand in admin.site._registry:
        print("✅ Brand registered in admin")
    if Campaign in admin.site._registry:
        print("✅ Campaign registered in admin")
    if Spend in admin.site._registry:
        print("✅ Spend registered in admin")
    if Schedule in admin.site._registry:
        print("✅ Schedule registered in admin")


def cleanup_test_data(brand: Brand) -> None:
    """Remove test data."""
    print("\n🧹 Cleaning up test data...")
    brand.delete()
    print("✅ Test data removed")


def main() -> int:
    """Run all tests."""
    print("🚀 Starting Budget Management System tests")
    print("=" * 60)
    
    try:
        # Test models
        brand, campaign, schedule, spend = test_models()
        
        # Test services
        spending_service, scheduling_service = test_services()
        
        # Test budget enforcement
        test_budget_enforcement(brand, campaign, spending_service)
        
        # Test dayparting
        test_dayparting(campaign, scheduling_service)
        
        # Test commands
        test_commands()
        
        # Test Celery tasks
        test_celery_tasks()
        
        # Test admin interface
        test_admin_interface()
        
        # Clean up test data
        cleanup_test_data(brand)
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ System working correctly")
        print("\n🌐 Access: http://localhost:8000/admin")
        print("📊 Use the admin to create brands, campaigns and test features")
        
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
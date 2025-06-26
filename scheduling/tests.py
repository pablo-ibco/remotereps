"""
Unit tests for scheduling app.
"""

from decimal import Decimal
from datetime import time, date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Schedule, DayOfWeek
from .services import SchedulingService
from brands.models import Brand
from campaigns.models import Campaign, CampaignStatus, PauseReason
from typing import List


class ScheduleModelTest(TestCase):
    """Test cases for Schedule model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('100.00'),
            monthly_budget=Decimal('1000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=CampaignStatus.ACTIVE
        )

    def test_schedule_creation(self) -> None:
        """Test schedule creation with valid data."""
        schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),  # 09:00
            end_time=time(18, 0),   # 18:00
            is_active=True
        )
        
        self.assertEqual(schedule.campaign, self.campaign)
        self.assertEqual(schedule.day_of_week, DayOfWeek.MONDAY)
        self.assertEqual(schedule.start_time, time(9, 0))
        self.assertEqual(schedule.end_time, time(18, 0))
        self.assertTrue(schedule.is_active)
        self.assertIsNotNone(schedule.id)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.updated_at)

    def test_schedule_str_representation(self) -> None:
        """Test string representation of schedule."""
        schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        expected = f"{self.campaign.name} - Monday 09:00:00-18:00:00"
        self.assertEqual(str(schedule), expected)

    def test_schedule_validation_end_time_after_start_time(self) -> None:
        """Test schedule validation when end_time is after start_time."""
        schedule = Schedule(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        # This should not raise an exception
        schedule.full_clean()

    def test_schedule_validation_end_time_before_start_time(self) -> None:
        """Test schedule validation when end_time is before start_time."""
        schedule = Schedule(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(18, 0),  # 18:00
            end_time=time(9, 0),     # 09:00 (before start)
            is_active=True
        )
        
        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_schedule_validation_end_time_equal_start_time(self) -> None:
        """Test schedule validation when end_time equals start_time."""
        schedule = Schedule(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(9, 0),  # Same as start
            is_active=True
        )
        
        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_is_time_in_range(self) -> None:
        """Test is_time_in_range method."""
        schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        # Test times within range
        self.assertTrue(schedule.is_time_in_range(time(9, 0)))   # Start time
        self.assertTrue(schedule.is_time_in_range(time(12, 0)))  # Middle
        self.assertTrue(schedule.is_time_in_range(time(18, 0)))  # End time
        
        # Test times outside range
        self.assertFalse(schedule.is_time_in_range(time(8, 59)))  # Before start
        self.assertFalse(schedule.is_time_in_range(time(18, 1)))  # After end

    def test_get_active_schedules_for_campaign(self) -> None:
        """Test get_active_schedules_for_campaign class method."""
        # Create active schedules
        schedule1 = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        schedule2 = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.TUESDAY,
            start_time=time(10, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create inactive schedule
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.WEDNESDAY,
            start_time=time(8, 0),
            end_time=time(16, 0),
            is_active=False
        )
        
        active_schedules = Schedule.get_active_schedules_for_campaign(self.campaign)
        self.assertEqual(len(active_schedules), 2)
        self.assertIn(schedule1, active_schedules)
        self.assertIn(schedule2, active_schedules)

    def test_get_schedule_for_campaign_and_day(self) -> None:
        """Test get_schedule_for_campaign_and_day class method."""
        schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        # Test existing schedule
        found_schedule = Schedule.get_schedule_for_campaign_and_day(self.campaign, DayOfWeek.MONDAY)
        self.assertEqual(found_schedule, schedule)
        
        # Test non-existing schedule
        found_schedule = Schedule.get_schedule_for_campaign_and_day(self.campaign, DayOfWeek.TUESDAY)
        self.assertIsNone(found_schedule)

    def test_is_campaign_scheduled_now(self) -> None:
        """Test is_campaign_scheduled_now class method."""
        # Create schedule for today
        today = timezone.now()
        current_day = today.weekday()  # 0=Monday, 6=Sunday
        
        schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=current_day,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        # Test that schedule exists for today
        found_schedule = Schedule.get_schedule_for_campaign_and_day(self.campaign, current_day)
        self.assertIsNotNone(found_schedule)
        self.assertEqual(found_schedule, schedule)

    def test_schedule_meta_options(self) -> None:
        """Test schedule meta options."""
        self.assertEqual(Schedule._meta.db_table, 'schedules')
        self.assertEqual(Schedule._meta.ordering, ['campaign__name', 'day_of_week', 'start_time'])
        self.assertEqual(Schedule._meta.verbose_name, 'Schedule')
        self.assertEqual(Schedule._meta.verbose_name_plural, 'Schedules')


class DayOfWeekTest(TestCase):
    """Test cases for DayOfWeek choices."""

    def test_day_of_week_choices(self) -> None:
        """Test day of week choices."""
        choices = DayOfWeek.choices
        choice_values = [choice[0] for choice in choices]
        choice_labels = [choice[1] for choice in choices]
        
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in expected_days:
            self.assertIn(day, choice_labels)
        
        # Check that we have 7 days (0-6)
        self.assertEqual(len(choices), 7)
        self.assertEqual(choice_values, list(range(7)))


class SchedulingServiceTest(TestCase):
    """Test cases for SchedulingService."""

    def setUp(self) -> None:
        """Set up test data."""
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('100.00'),
            monthly_budget=Decimal('1000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=CampaignStatus.ACTIVE
        )
        self.service = SchedulingService()

    def test_is_campaign_scheduled_now_with_schedule(self) -> None:
        """Test is_campaign_scheduled_now when campaign has active schedule."""
        # Create schedule for current day and time
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()
        
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=current_day,
            start_time=time(current_time.hour - 1, current_time.minute),
            end_time=time(current_time.hour + 1, current_time.minute),
            is_active=True
        )
        
        self.assertTrue(self.service.is_campaign_scheduled_now(self.campaign))

    def test_is_campaign_scheduled_now_without_schedule(self) -> None:
        """Test is_campaign_scheduled_now when campaign has no schedule."""
        self.assertFalse(self.service.is_campaign_scheduled_now(self.campaign))

    def test_get_campaigns_that_should_be_active(self) -> None:
        """Test get_campaigns_that_should_be_active method."""
        # Create another campaign with schedule
        campaign2 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            status=CampaignStatus.ACTIVE
        )
        
        # Create schedule for current day and time
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()
        
        Schedule.objects.create(
            campaign=campaign2,
            day_of_week=current_day,
            start_time=time(current_time.hour - 1, current_time.minute),
            end_time=time(current_time.hour + 1, current_time.minute),
            is_active=True
        )
        
        active_campaigns = self.service.get_campaigns_that_should_be_active()
        self.assertIn(campaign2, active_campaigns)
        self.assertNotIn(self.campaign, active_campaigns)

    def test_get_campaigns_that_should_be_paused(self) -> None:
        """Test get_campaigns_that_should_be_paused method."""
        # Create schedule for different day
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=(timezone.now().weekday() + 1) % 7,  # Different day
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        paused_campaigns = self.service.get_campaigns_that_should_be_paused()
        self.assertIn(self.campaign, paused_campaigns)

    def test_enforce_dayparting(self) -> None:
        """Test enforce_dayparting method."""
        # Create schedule for different day
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=(timezone.now().weekday() + 1) % 7,  # Different day
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        result = self.service.enforce_dayparting()
        self.assertIn('paused', result)
        self.assertIn('activated', result)
        self.assertIn('errors', result)

    def test_create_default_schedule(self) -> None:
        """Test create_default_schedule method."""
        schedule = self.service.create_default_schedule(self.campaign)
        
        self.assertEqual(schedule.campaign, self.campaign)
        self.assertEqual(schedule.day_of_week, 0)  # Monday
        self.assertEqual(schedule.start_time, time(0, 0))  # 00:00 (24/7 schedule)
        self.assertEqual(schedule.end_time, time(23, 59, 59))  # 23:59:59
        self.assertTrue(schedule.is_active)

    def test_get_campaign_schedule_summary(self) -> None:
        """Test get_campaign_schedule_summary method."""
        # Create schedules for different days
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.TUESDAY,
            start_time=time(10, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        summary = self.service.get_campaign_schedule_summary(self.campaign)
        self.assertIn('campaign_id', summary)
        self.assertIn('campaign_name', summary)
        self.assertIn('total_schedules', summary)
        self.assertIn('schedules_by_day', summary)
        self.assertIn('is_scheduled_now', summary)
        self.assertEqual(summary['total_schedules'], 2)

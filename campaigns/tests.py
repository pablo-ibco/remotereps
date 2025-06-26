"""
Unit tests for campaigns app.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Campaign, CampaignStatus, PauseReason
from brands.models import Brand


class CampaignModelTest(TestCase):
    """Test cases for Campaign model."""

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

    def test_campaign_creation(self) -> None:
        """Test campaign creation with valid data."""
        self.assertEqual(self.campaign.name, "Test Campaign")
        self.assertEqual(self.campaign.brand, self.brand)
        self.assertEqual(self.campaign.status, CampaignStatus.ACTIVE)
        self.assertEqual(self.campaign.daily_spend, Decimal('0.00'))
        self.assertEqual(self.campaign.monthly_spend, Decimal('0.00'))
        self.assertIsNone(self.campaign.pause_reason)
        self.assertIsNone(self.campaign.paused_at)
        self.assertIsNotNone(self.campaign.id)
        self.assertIsNotNone(self.campaign.created_at)
        self.assertIsNotNone(self.campaign.updated_at)

    def test_campaign_str_representation(self) -> None:
        """Test string representation of campaign."""
        expected = f"{self.brand.name} - {self.campaign.name}"
        self.assertEqual(str(self.campaign), expected)

    def test_campaign_unique_together(self) -> None:
        """Test that campaign names must be unique per brand."""
        # This should work (same name, different brand)
        brand2 = Brand.objects.create(
            name="Test Brand 2",
            daily_budget=Decimal('50.00'),
            monthly_budget=Decimal('500.00')
        )
        Campaign.objects.create(
            brand=brand2,
            name="Test Campaign",  # Same name, different brand
            status=CampaignStatus.ACTIVE
        )

        # This should fail (same name, same brand)
        with self.assertRaises(Exception):  # IntegrityError
            Campaign.objects.create(
                brand=self.brand,
                name="Test Campaign",  # Same name, same brand
                status=CampaignStatus.ACTIVE
            )

    def test_is_active(self) -> None:
        """Test is_active method."""
        self.assertTrue(self.campaign.is_active())
        
        self.campaign.status = CampaignStatus.PAUSED
        self.assertFalse(self.campaign.is_active())

    def test_is_paused(self) -> None:
        """Test is_paused method."""
        self.assertFalse(self.campaign.is_paused())
        
        self.campaign.status = CampaignStatus.PAUSED
        self.assertTrue(self.campaign.is_paused())

    def test_pause_campaign(self) -> None:
        """Test pause method."""
        self.campaign.pause(PauseReason.DAILY_BUDGET_EXCEEDED)
        
        self.assertEqual(self.campaign.status, CampaignStatus.PAUSED)
        self.assertEqual(self.campaign.pause_reason, PauseReason.DAILY_BUDGET_EXCEEDED)
        self.assertIsNotNone(self.campaign.paused_at)

    def test_activate_campaign(self) -> None:
        """Test activate method."""
        # First pause the campaign
        self.campaign.pause(PauseReason.DAILY_BUDGET_EXCEEDED)
        
        # Create a default schedule so campaign can be activated
        from scheduling.services import SchedulingService
        service = SchedulingService()
        service.create_default_schedule(self.campaign)
        
        # Then activate it
        result = self.campaign.activate()
        
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, CampaignStatus.ACTIVE)
        self.assertIsNone(self.campaign.pause_reason)
        self.assertIsNone(self.campaign.paused_at)

    def test_can_be_activated_when_under_budget(self) -> None:
        """Test can_be_activated when under budget."""
        self.campaign.daily_spend = Decimal('50.00')
        self.campaign.monthly_spend = Decimal('500.00')
        self.campaign.save()
        
        # Create a default schedule so campaign can be activated
        from scheduling.services import SchedulingService
        service = SchedulingService()
        service.create_default_schedule(self.campaign)
        
        self.assertTrue(self.campaign.can_be_activated())

    def test_can_be_activated_when_over_daily_budget(self) -> None:
        """Test can_be_activated when over daily budget."""
        self.campaign.daily_spend = Decimal('120.00')  # Over daily budget
        self.campaign.monthly_spend = Decimal('500.00')
        self.campaign.save()
        
        self.assertFalse(self.campaign.can_be_activated())

    def test_can_be_activated_when_over_monthly_budget(self) -> None:
        """Test can_be_activated when over monthly budget."""
        self.campaign.daily_spend = Decimal('50.00')
        self.campaign.monthly_spend = Decimal('1200.00')  # Over monthly budget
        self.campaign.save()
        
        self.assertFalse(self.campaign.can_be_activated())

    def test_add_spend(self) -> None:
        """Test add_spend method."""
        initial_daily = self.campaign.daily_spend
        initial_monthly = self.campaign.monthly_spend
        
        self.campaign.add_spend(Decimal('25.00'))
        
        self.assertEqual(self.campaign.daily_spend, initial_daily + Decimal('25.00'))
        self.assertEqual(self.campaign.monthly_spend, initial_monthly + Decimal('25.00'))

    def test_add_spend_negative_amount(self) -> None:
        """Test add_spend with negative amount."""
        with self.assertRaises(ValueError):
            self.campaign.add_spend(Decimal('-10.00'))

    def test_add_spend_zero_amount(self) -> None:
        """Test add_spend with zero amount."""
        with self.assertRaises(ValueError):
            self.campaign.add_spend(Decimal('0.00'))

    def test_reset_daily_spend(self) -> None:
        """Test reset_daily_spend method."""
        self.campaign.daily_spend = Decimal('50.00')
        self.campaign.save()
        
        self.campaign.reset_daily_spend()
        
        self.assertEqual(self.campaign.daily_spend, Decimal('0.00'))

    def test_reset_monthly_spend(self) -> None:
        """Test reset_monthly_spend method."""
        self.campaign.monthly_spend = Decimal('500.00')
        self.campaign.save()
        
        self.campaign.reset_monthly_spend()
        
        self.assertEqual(self.campaign.monthly_spend, Decimal('0.00'))

    def test_get_daily_spend(self) -> None:
        """Test get_daily_spend method."""
        self.campaign.daily_spend = Decimal('25.50')
        self.campaign.save()
        
        self.assertEqual(self.campaign.get_daily_spend(), Decimal('25.50'))

    def test_get_monthly_spend(self) -> None:
        """Test get_monthly_spend method."""
        self.campaign.monthly_spend = Decimal('250.75')
        self.campaign.save()
        
        self.assertEqual(self.campaign.get_monthly_spend(), Decimal('250.75'))

    def test_get_remaining_daily_budget(self) -> None:
        """Test get_remaining_daily_budget method."""
        self.campaign.daily_spend = Decimal('30.00')
        self.campaign.save()
        
        expected_remaining = Decimal('100.00') - Decimal('30.00')
        self.assertEqual(self.campaign.get_remaining_daily_budget(), expected_remaining)

    def test_get_remaining_monthly_budget(self) -> None:
        """Test get_remaining_monthly_budget method."""
        self.campaign.monthly_spend = Decimal('300.00')
        self.campaign.save()
        
        expected_remaining = Decimal('1000.00') - Decimal('300.00')
        self.assertEqual(self.campaign.get_remaining_monthly_budget(), expected_remaining)

    def test_campaign_meta_options(self) -> None:
        """Test campaign meta options."""
        self.assertEqual(Campaign._meta.db_table, 'campaigns')
        self.assertEqual(Campaign._meta.ordering, ['brand__name', 'name'])
        self.assertEqual(Campaign._meta.verbose_name, 'Campaign')
        self.assertEqual(Campaign._meta.verbose_name_plural, 'Campaigns')


class CampaignStatusTest(TestCase):
    """Test cases for CampaignStatus choices."""

    def test_campaign_status_choices(self) -> None:
        """Test campaign status choices."""
        choices = CampaignStatus.choices
        choice_values = [choice[0] for choice in choices]
        choice_labels = [choice[1] for choice in choices]
        
        expected_statuses = ['Active', 'Paused']
        
        for status in expected_statuses:
            self.assertIn(status, choice_labels)
        
        # Check that we have 2 statuses
        self.assertEqual(len(choices), 2)
        self.assertIn('ACTIVE', choice_values)
        self.assertIn('PAUSED', choice_values)


class PauseReasonTest(TestCase):
    """Test cases for PauseReason choices."""

    def test_pause_reason_choices(self) -> None:
        """Test pause reason choices."""
        choices = PauseReason.choices
        choice_values = [choice[0] for choice in choices]
        choice_labels = [choice[1] for choice in choices]
        
        expected_reasons = [
            'Daily Budget Exceeded',
            'Monthly Budget Exceeded',
            'Outside Schedule',
            'No Schedule',
            'Manual Pause'
        ]
        
        for reason in expected_reasons:
            self.assertIn(reason, choice_labels)
        
        # Check that we have 5 reasons
        self.assertEqual(len(choices), 5)
        self.assertIn('DAILY_BUDGET_EXCEEDED', choice_values)
        self.assertIn('MONTHLY_BUDGET_EXCEEDED', choice_values)
        self.assertIn('OUTSIDE_SCHEDULE', choice_values)
        self.assertIn('NO_SCHEDULE', choice_values)
        self.assertIn('MANUAL', choice_values)

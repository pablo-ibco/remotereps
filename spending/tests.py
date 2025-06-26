"""
Unit tests for spending app.
"""

from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Spend, SpendType
from .services import SpendingService
from brands.models import Brand
from campaigns.models import Campaign, CampaignStatus


class SpendModelTest(TestCase):
    """Test cases for Spend model."""

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

    def test_spend_creation(self) -> None:
        """Test spend creation with valid data."""
        spend = Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY,
            description="Test spend"
        )
        
        self.assertEqual(spend.campaign, self.campaign)
        self.assertEqual(spend.amount, Decimal('25.00'))
        self.assertEqual(spend.spend_date, date.today())
        self.assertEqual(spend.spend_type, SpendType.DAILY)
        self.assertEqual(spend.description, "Test spend")
        self.assertIsNotNone(spend.id)
        self.assertIsNotNone(spend.created_at)

    def test_spend_str_representation(self) -> None:
        """Test string representation of spend."""
        spend = Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY,
            description="Test spend"
        )
        
        expected = f"{self.campaign.name} - 25.00 on {date.today()}"
        self.assertEqual(str(spend), expected)

    def test_spend_validation_negative_amount(self) -> None:
        """Test spend validation with negative amount."""
        with self.assertRaises(ValidationError):
            spend = Spend(
                campaign=self.campaign,
                amount=Decimal('-10.00'),
                spend_date=date.today(),
                spend_type=SpendType.DAILY
            )
            spend.full_clean()

    def test_spend_save_updates_campaign_totals(self) -> None:
        """Test that saving a spend updates campaign totals."""
        initial_daily = self.campaign.daily_spend
        initial_monthly = self.campaign.monthly_spend
        
        # Create spend using the model instance to trigger custom save
        spend = Spend(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY
        )
        spend.save()
        
        # Fetch a fresh instance of campaign from DB before assertions
        campaign = type(self.campaign).objects.get(pk=self.campaign.pk)
        campaign.refresh_from_db()
        self.assertEqual(campaign.daily_spend, initial_daily + Decimal('25.00'))
        self.assertEqual(campaign.monthly_spend, initial_monthly + Decimal('25.00'))

    def test_get_daily_spend_for_campaign(self) -> None:
        """Test get_daily_spend_for_campaign class method."""
        # Create spends for today
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY
        )
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('15.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY
        )
        
        # Create spend for different date
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('10.00'),
            spend_date=date(2024, 1, 1),
            spend_type=SpendType.DAILY
        )
        
        total = Spend.get_daily_spend_for_campaign(self.campaign, date.today())
        self.assertEqual(total, Decimal('40.00'))

    def test_get_monthly_spend_for_campaign(self) -> None:
        """Test get_monthly_spend_for_campaign class method."""
        current_year = date.today().year
        current_month = date.today().month
        
        # Create spends for current month
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('100.00'),
            spend_date=date(current_year, current_month, 1),
            spend_type=SpendType.MONTHLY
        )
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('200.00'),
            spend_date=date(current_year, current_month, 15),
            spend_type=SpendType.MONTHLY
        )
        
        # Create spend for different month
        Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('50.00'),
            spend_date=date(current_year, current_month - 1, 1),
            spend_type=SpendType.MONTHLY
        )
        
        total = Spend.get_monthly_spend_for_campaign(self.campaign, current_year, current_month)
        self.assertEqual(total, Decimal('300.00'))

    def test_get_daily_spend_for_brand(self) -> None:
        """Test get_daily_spend_for_brand class method."""
        campaign2 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            daily_spend=Decimal('30.00'),
            status=CampaignStatus.ACTIVE
        )
        
        self.campaign.daily_spend = Decimal('25.00')
        self.campaign.save()
        
        total = Spend.get_daily_spend_for_brand(self.brand.id)
        self.assertEqual(total, Decimal('55.00'))

    def test_get_monthly_spend_for_brand(self) -> None:
        """Test get_monthly_spend_for_brand class method."""
        campaign2 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            monthly_spend=Decimal('300.00'),
            status=CampaignStatus.ACTIVE
        )
        
        self.campaign.monthly_spend = Decimal('250.00')
        self.campaign.save()
        
        total = Spend.get_monthly_spend_for_brand(self.brand.id)
        self.assertEqual(total, Decimal('550.00'))

    def test_spend_meta_options(self) -> None:
        """Test spend meta options."""
        self.assertEqual(Spend._meta.db_table, 'spends')
        self.assertEqual(Spend._meta.ordering, ['-spend_date', '-created_at'])
        self.assertEqual(Spend._meta.verbose_name, 'Spend')
        self.assertEqual(Spend._meta.verbose_name_plural, 'Spends')


class SpendTypeTest(TestCase):
    """Test cases for SpendType choices."""

    def test_spend_type_choices(self) -> None:
        """Test spend type choices."""
        choices = SpendType.choices
        choice_values = [choice[0] for choice in choices]
        choice_labels = [choice[1] for choice in choices]
        
        self.assertIn('DAILY', choice_values)
        self.assertIn('MONTHLY', choice_values)
        self.assertIn('Daily', choice_labels)
        self.assertIn('Monthly', choice_labels)


class SpendingServiceTest(TestCase):
    """Test cases for SpendingService."""

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
        self.service = SpendingService()

    def test_track_spend(self) -> None:
        """Test track_spend method."""
        spend = self.service.track_spend(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            description="Test spend"
        )
        
        self.assertEqual(spend.campaign, self.campaign)
        self.assertEqual(spend.amount, Decimal('25.00'))
        self.assertEqual(spend.spend_date, date.today())
        self.assertEqual(spend.description, "Test spend")
        
        # Fetch a fresh instance of campaign from DB before assertions
        campaign = type(self.campaign).objects.get(pk=self.campaign.pk)
        self.assertEqual(campaign.daily_spend, Decimal('25.00'))
        self.assertEqual(campaign.monthly_spend, Decimal('25.00'))

    def test_track_spend_with_custom_date(self) -> None:
        """Test track_spend with custom date."""
        custom_date = date(2024, 1, 15)
        spend = self.service.track_spend(
            campaign=self.campaign,
            amount=Decimal('30.00'),
            spend_date=custom_date,
            description="Custom date spend"
        )
        
        self.assertEqual(spend.spend_date, custom_date)

    def test_check_budget_limits_under_budget(self) -> None:
        """Test check_budget_limits when under budget."""
        self.campaign.daily_spend = Decimal('50.00')
        self.campaign.monthly_spend = Decimal('500.00')
        self.campaign.save()
        
        results = self.service.check_budget_limits(self.campaign)
        
        self.assertFalse(results['daily_exceeded'])
        self.assertFalse(results['monthly_exceeded'])
        self.assertIsNone(results['action_taken'])

    def test_check_budget_limits_over_daily_budget(self) -> None:
        """Test check_budget_limits when over daily budget."""
        self.campaign.daily_spend = Decimal('120.00')  # Over daily budget
        self.campaign.monthly_spend = Decimal('500.00')
        self.campaign.save()
        
        results = self.service.check_budget_limits(self.campaign)
        
        self.assertTrue(results['daily_exceeded'])
        self.assertFalse(results['monthly_exceeded'])
        self.assertEqual(results['action_taken'], 'paused_daily')
        
        # Check that campaign was paused
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, CampaignStatus.PAUSED)

    def test_check_budget_limits_over_monthly_budget(self) -> None:
        """Test check_budget_limits when over monthly budget."""
        self.campaign.daily_spend = Decimal('50.00')
        self.campaign.monthly_spend = Decimal('1200.00')  # Over monthly budget
        self.campaign.save()
        
        results = self.service.check_budget_limits(self.campaign)
        
        self.assertFalse(results['daily_exceeded'])
        self.assertTrue(results['monthly_exceeded'])
        self.assertEqual(results['action_taken'], 'paused_monthly')
        
        # Check that campaign was paused
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, CampaignStatus.PAUSED)

    def test_get_spending_summary(self) -> None:
        """Test get_spending_summary method."""
        # Set campaign spend values directly
        self.campaign.daily_spend = Decimal('25.00')
        self.campaign.monthly_spend = Decimal('250.00')
        self.campaign.save()
        
        summary = self.service.get_spending_summary(self.campaign)
        
        self.assertEqual(summary['campaign_id'], str(self.campaign.id))
        self.assertEqual(summary['campaign_name'], self.campaign.name)
        self.assertEqual(summary['brand_name'], self.brand.name)
        self.assertEqual(summary['daily_spend'], 0.0)
        self.assertEqual(summary['monthly_spend'], 0.0)
        self.assertEqual(summary['daily_budget'], 100.0)
        self.assertEqual(summary['monthly_budget'], 1000.0)
        self.assertEqual(summary['status'], CampaignStatus.ACTIVE)

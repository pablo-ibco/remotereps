"""
Unit tests for brands app.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Brand
from campaigns.models import Campaign, CampaignStatus


class BrandModelTest(TestCase):
    """Test cases for Brand model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('100.00'),
            monthly_budget=Decimal('1000.00')
        )

    def test_brand_creation(self) -> None:
        """Test brand creation with valid data."""
        self.assertEqual(self.brand.name, "Test Brand")
        self.assertEqual(self.brand.daily_budget, Decimal('100.00'))
        self.assertEqual(self.brand.monthly_budget, Decimal('1000.00'))
        self.assertIsNotNone(self.brand.id)
        self.assertIsNotNone(self.brand.created_at)
        self.assertIsNotNone(self.brand.updated_at)

    def test_brand_str_representation(self) -> None:
        """Test string representation of brand."""
        self.assertEqual(str(self.brand), "Test Brand")

    def test_brand_unique_name(self) -> None:
        """Test that brand names must be unique."""
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            Brand.objects.create(
                name="Test Brand",  # Same name
                daily_budget=Decimal('50.00'),
                monthly_budget=Decimal('500.00')
            )

    def test_brand_budget_validation(self) -> None:
        """Test budget validation."""
        # Test negative budget
        with self.assertRaises(ValidationError):
            brand = Brand(
                name="Invalid Brand",
                daily_budget=Decimal('-10.00'),
                monthly_budget=Decimal('100.00')
            )
            brand.full_clean()

    def test_get_daily_budget(self) -> None:
        """Test get_daily_budget method."""
        self.assertEqual(self.brand.get_daily_budget(), Decimal('100.00'))

    def test_get_monthly_budget(self) -> None:
        """Test get_monthly_budget method."""
        self.assertEqual(self.brand.get_monthly_budget(), Decimal('1000.00'))

    def test_get_total_campaigns_empty(self) -> None:
        """Test get_total_campaigns when no campaigns exist."""
        self.assertEqual(self.brand.get_total_campaigns(), 0)

    def test_get_total_campaigns_with_campaigns(self) -> None:
        """Test get_total_campaigns when campaigns exist."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 1",
            status=CampaignStatus.ACTIVE
        )
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            status=CampaignStatus.PAUSED
        )
        self.assertEqual(self.brand.get_total_campaigns(), 2)

    def test_get_total_daily_spend_empty(self) -> None:
        """Test get_total_daily_spend when no campaigns exist."""
        self.assertEqual(self.brand.get_total_daily_spend(), Decimal('0.00'))

    def test_get_total_daily_spend_with_campaigns(self) -> None:
        """Test get_total_daily_spend with campaigns."""
        campaign1 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 1",
            daily_spend=Decimal('25.00'),
            status=CampaignStatus.ACTIVE
        )
        campaign2 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            daily_spend=Decimal('35.00'),
            status=CampaignStatus.ACTIVE
        )
        expected_total = Decimal('25.00') + Decimal('35.00')
        self.assertEqual(self.brand.get_total_daily_spend(), expected_total)

    def test_get_total_monthly_spend_empty(self) -> None:
        """Test get_total_monthly_spend when no campaigns exist."""
        self.assertEqual(self.brand.get_total_monthly_spend(), Decimal('0.00'))

    def test_get_total_monthly_spend_with_campaigns(self) -> None:
        """Test get_total_monthly_spend with campaigns."""
        campaign1 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 1",
            monthly_spend=Decimal('250.00'),
            status=CampaignStatus.ACTIVE
        )
        campaign2 = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign 2",
            monthly_spend=Decimal('350.00'),
            status=CampaignStatus.ACTIVE
        )
        expected_total = Decimal('250.00') + Decimal('350.00')
        self.assertEqual(self.brand.get_total_monthly_spend(), expected_total)

    def test_get_remaining_daily_budget(self) -> None:
        """Test get_remaining_daily_budget calculation."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_spend=Decimal('30.00'),
            status=CampaignStatus.ACTIVE
        )
        expected_remaining = Decimal('100.00') - Decimal('30.00')
        self.assertEqual(self.brand.get_remaining_daily_budget(), expected_remaining)

    def test_get_remaining_monthly_budget(self) -> None:
        """Test get_remaining_monthly_budget calculation."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            monthly_spend=Decimal('300.00'),
            status=CampaignStatus.ACTIVE
        )
        expected_remaining = Decimal('1000.00') - Decimal('300.00')
        self.assertEqual(self.brand.get_remaining_monthly_budget(), expected_remaining)

    def test_is_over_daily_budget_false(self) -> None:
        """Test is_over_daily_budget when under budget."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_spend=Decimal('50.00'),
            status=CampaignStatus.ACTIVE
        )
        self.assertFalse(self.brand.is_over_daily_budget())

    def test_is_over_daily_budget_true(self) -> None:
        """Test is_over_daily_budget when over budget."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_spend=Decimal('120.00'),
            status=CampaignStatus.ACTIVE
        )
        self.assertTrue(self.brand.is_over_daily_budget())

    def test_is_over_monthly_budget_false(self) -> None:
        """Test is_over_monthly_budget when under budget."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            monthly_spend=Decimal('500.00'),
            status=CampaignStatus.ACTIVE
        )
        self.assertFalse(self.brand.is_over_monthly_budget())

    def test_is_over_monthly_budget_true(self) -> None:
        """Test is_over_monthly_budget when over budget."""
        Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            monthly_spend=Decimal('1200.00'),
            status=CampaignStatus.ACTIVE
        )
        self.assertTrue(self.brand.is_over_monthly_budget())

    def test_brand_meta_options(self) -> None:
        """Test brand meta options."""
        self.assertEqual(Brand._meta.db_table, 'brands')
        self.assertEqual(Brand._meta.ordering, ['name'])
        self.assertEqual(Brand._meta.verbose_name, 'Brand')
        self.assertEqual(Brand._meta.verbose_name_plural, 'Brands')

#!/usr/bin/env python
"""
Comprehensive API Test Suite for Budget Management System
Tests all REST endpoints, CRUD operations, validations, and integrations.
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import time, date, datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')
django.setup()

from brands.models import Brand
from campaigns.models import Campaign, CampaignStatus, PauseReason
from spending.models import Spend, SpendType
from scheduling.models import Schedule, DayOfWeek


class BaseAPITestCase(TestCase):
    """Base test case with common setup and utilities."""
    
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.base_url = '/api'
        
        # Create test brand
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('100.00'),
            monthly_budget=Decimal('1000.00')
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=CampaignStatus.ACTIVE
        )
        
        # Create test schedule
        self.schedule = Schedule.objects.create(
            campaign=self.campaign,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        # Create test spend
        self.spend = Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal('25.00'),
            spend_date=date.today(),
            spend_type=SpendType.DAILY,
            description="Test spend"
        )

    def assert_response_success(self, response, expected_status=status.HTTP_200_OK):
        """Assert that response is successful."""
        self.assertEqual(response.status_code, expected_status)
        self.assertIsInstance(response.data, (list, dict))

    def assert_response_error(self, response, expected_status=status.HTTP_400_BAD_REQUEST):
        """Assert that response is an error."""
        self.assertEqual(response.status_code, expected_status)
        self.assertIsInstance(response.data, dict)


class BrandAPITests(BaseAPITestCase):
    """Test Brand API endpoints."""
    
    def test_list_brands(self):
        """Test GET /api/brands/ - List all brands."""
        url = f'{self.base_url}/brands/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check brand data structure
        brand_data = response.data[0]
        self.assertIn('id', brand_data)
        self.assertIn('name', brand_data)
        self.assertIn('daily_budget', brand_data)
        self.assertIn('monthly_budget', brand_data)
        self.assertIn('created_at', brand_data)
        self.assertIn('updated_at', brand_data)

    def test_create_brand_success(self):
        """Test POST /api/brands/ - Create brand successfully."""
        url = f'{self.base_url}/brands/'
        data = {
            'name': 'New Brand',
            'daily_budget': '150.00',
            'monthly_budget': '3000.00'
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_response_success(response, status.HTTP_201_CREATED)
        
        # Verify brand was created
        self.assertEqual(response.data['name'], 'New Brand')
        self.assertEqual(response.data['daily_budget'], '150.00')
        self.assertEqual(response.data['monthly_budget'], '3000.00')
        
        # Check database
        brand = Brand.objects.get(name='New Brand')
        self.assertEqual(brand.daily_budget, Decimal('150.00'))

    def test_create_brand_validation_error(self):
        """Test POST /api/brands/ - Validation errors."""
        url = f'{self.base_url}/brands/'
        
        # Test missing required fields
        data = {}
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)
        self.assertIn('name', response.data)
        
        # Test duplicate name
        data = {
            'name': 'Test Brand',  # Already exists
            'daily_budget': '100.00',
            'monthly_budget': '1000.00'
        }
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)
        self.assertIn('name', response.data)
        
        # Test invalid budget values
        data = {
            'name': 'Invalid Brand',
            'daily_budget': '-50.00',  # Negative value
            'monthly_budget': '1000.00'
        }
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)

    def test_retrieve_brand(self):
        """Test GET /api/brands/{id}/ - Retrieve specific brand."""
        url = f'{self.base_url}/brands/{self.brand.id}/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertEqual(response.data['id'], str(self.brand.id))
        self.assertEqual(response.data['name'], self.brand.name)

    def test_retrieve_brand_not_found(self):
        """Test GET /api/brands/{id}/ - Brand not found."""
        url = f'{self.base_url}/brands/99999999-9999-9999-9999-999999999999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_brand(self):
        """Test PUT /api/brands/{id}/ - Update brand."""
        url = f'{self.base_url}/brands/{self.brand.id}/'
        data = {
            'name': 'Updated Brand',
            'daily_budget': '200.00',
            'monthly_budget': '4000.00'
        }
        
        response = self.client.put(url, data, format='json')
        self.assert_response_success(response)
        
        # Verify updates
        self.assertEqual(response.data['name'], 'Updated Brand')
        self.assertEqual(response.data['daily_budget'], '200.00')
        
        # Check database
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.name, 'Updated Brand')

    def test_partial_update_brand(self):
        """Test PATCH /api/brands/{id}/ - Partial update brand."""
        url = f'{self.base_url}/brands/{self.brand.id}/'
        data = {'name': 'Patched Brand'}
        
        response = self.client.patch(url, data, format='json')
        self.assert_response_success(response)
        
        # Verify only name was updated
        self.assertEqual(response.data['name'], 'Patched Brand')
        self.assertEqual(response.data['daily_budget'], '100.00')  # Unchanged

    def test_delete_brand(self):
        """Test DELETE /api/brands/{id}/ - Delete brand."""
        url = f'{self.base_url}/brands/{self.brand.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify brand was deleted
        with self.assertRaises(Brand.DoesNotExist):
            Brand.objects.get(id=self.brand.id)


class CampaignAPITests(BaseAPITestCase):
    """Test Campaign API endpoints."""
    
    def test_list_campaigns(self):
        """Test GET /api/campaigns/ - List all campaigns."""
        url = f'{self.base_url}/campaigns/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check campaign data structure
        campaign_data = response.data[0]
        self.assertIn('id', campaign_data)
        self.assertIn('brand', campaign_data)
        self.assertIn('name', campaign_data)
        self.assertIn('status', campaign_data)
        self.assertIn('daily_spend', campaign_data)
        self.assertIn('monthly_spend', campaign_data)

    def test_create_campaign_success(self):
        """Test POST /api/campaigns/ - Create campaign successfully."""
        url = f'{self.base_url}/campaigns/'
        data = {
            'brand': str(self.brand.id),
            'name': 'New Campaign',
            'status': CampaignStatus.ACTIVE
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_response_success(response, status.HTTP_201_CREATED)
        
        # Verify campaign was created
        self.assertEqual(response.data['name'], 'New Campaign')
        self.assertEqual(response.data['status'], CampaignStatus.ACTIVE)
        self.assertEqual(str(response.data['brand']), str(self.brand.id))

    def test_create_campaign_validation_error(self):
        """Test POST /api/campaigns/ - Validation errors."""
        url = f'{self.base_url}/campaigns/'
        
        # Test missing required fields
        data = {}
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)
        self.assertIn('brand', response.data)
        self.assertIn('name', response.data)
        
        # Test invalid brand ID
        data = {
            'brand': '99999999-9999-9999-9999-999999999999',
            'name': 'Invalid Campaign'
        }
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)

    def test_retrieve_campaign(self):
        """Test GET /api/campaigns/{id}/ - Retrieve specific campaign."""
        url = f'{self.base_url}/campaigns/{self.campaign.id}/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertEqual(response.data['id'], str(self.campaign.id))
        self.assertEqual(response.data['name'], self.campaign.name)
        self.assertEqual(str(response.data['brand']), str(self.brand.id))

    def test_update_campaign(self):
        """Test PUT /api/campaigns/{id}/ - Update campaign."""
        url = f'{self.base_url}/campaigns/{self.campaign.id}/'
        data = {
            'brand': str(self.brand.id),
            'name': 'Updated Campaign',
            'status': CampaignStatus.PAUSED,
            'pause_reason': 'DAILY_BUDGET_EXCEEDED'
        }
        
        response = self.client.put(url, data, format='json')
        self.assert_response_success(response)
        
        # Verify updates
        self.assertEqual(response.data['name'], 'Updated Campaign')
        self.assertEqual(response.data['status'], CampaignStatus.PAUSED)
        self.assertEqual(response.data['pause_reason'], 'DAILY_BUDGET_EXCEEDED')

    def test_delete_campaign(self):
        """Test DELETE /api/campaigns/{id}/ - Delete campaign."""
        url = f'{self.base_url}/campaigns/{self.campaign.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify campaign was deleted
        with self.assertRaises(Campaign.DoesNotExist):
            Campaign.objects.get(id=self.campaign.id)


class SpendAPITests(BaseAPITestCase):
    """Test Spend API endpoints."""
    
    def test_list_spends(self):
        """Test GET /api/spends/ - List all spends."""
        url = f'{self.base_url}/spends/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check spend data structure
        spend_data = response.data[0]
        self.assertIn('id', spend_data)
        self.assertIn('campaign', spend_data)
        self.assertIn('amount', spend_data)
        self.assertIn('spend_date', spend_data)
        self.assertIn('spend_type', spend_data)
        self.assertIn('description', spend_data)

    def test_create_spend_success(self):
        """Test POST /api/spends/ - Create spend successfully."""
        url = f'{self.base_url}/spends/'
        data = {
            'campaign': str(self.campaign.id),
            'amount': '50.00',
            'spend_date': date.today().isoformat(),
            'spend_type': SpendType.DAILY,
            'description': 'New spend'
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_response_success(response, status.HTTP_201_CREATED)
        
        # Verify spend was created
        self.assertEqual(response.data['amount'], '50.00')
        self.assertEqual(response.data['spend_type'], SpendType.DAILY)
        self.assertEqual(str(response.data['campaign']), str(self.campaign.id))

    def test_create_spend_validation_error(self):
        """Test POST /api/spends/ - Validation errors."""
        url = f'{self.base_url}/spends/'
        
        # Test missing required fields
        data = {}
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)
        self.assertIn('campaign', response.data)
        self.assertIn('amount', response.data)
        
        # Test invalid amount
        data = {
            'campaign': str(self.campaign.id),
            'amount': '-10.00',  # Negative amount
            'spend_date': date.today().isoformat(),
            'spend_type': SpendType.DAILY
        }
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)

    def test_retrieve_spend(self):
        """Test GET /api/spends/{id}/ - Retrieve specific spend."""
        url = f'{self.base_url}/spends/{self.spend.id}/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertEqual(response.data['id'], str(self.spend.id))
        self.assertEqual(response.data['amount'], '25.00')
        self.assertEqual(str(response.data['campaign']), str(self.campaign.id))

    def test_update_spend(self):
        """Test PUT /api/spends/{id}/ - Update spend."""
        url = f'{self.base_url}/spends/{self.spend.id}/'
        data = {
            'campaign': str(self.campaign.id),
            'amount': '75.00',
            'spend_date': date.today().isoformat(),
            'spend_type': SpendType.MONTHLY,
            'description': 'Updated spend'
        }
        
        response = self.client.put(url, data, format='json')
        self.assert_response_success(response)
        
        # Verify updates
        self.assertEqual(response.data['amount'], '75.00')
        self.assertEqual(response.data['spend_type'], SpendType.MONTHLY)
        self.assertEqual(response.data['description'], 'Updated spend')

    def test_delete_spend(self):
        """Test DELETE /api/spends/{id}/ - Delete spend."""
        url = f'{self.base_url}/spends/{self.spend.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify spend was deleted
        with self.assertRaises(Spend.DoesNotExist):
            Spend.objects.get(id=self.spend.id)


class ScheduleAPITests(BaseAPITestCase):
    """Test Schedule API endpoints."""
    
    def test_list_schedules(self):
        """Test GET /api/schedules/ - List all schedules."""
        url = f'{self.base_url}/schedules/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check schedule data structure
        schedule_data = response.data[0]
        self.assertIn('id', schedule_data)
        self.assertIn('campaign', schedule_data)
        self.assertIn('day_of_week', schedule_data)
        self.assertIn('start_time', schedule_data)
        self.assertIn('end_time', schedule_data)
        self.assertIn('is_active', schedule_data)

    def test_create_schedule_success(self):
        """Test POST /api/schedules/ - Create schedule successfully."""
        url = f'{self.base_url}/schedules/'
        data = {
            'campaign': str(self.campaign.id),
            'day_of_week': DayOfWeek.TUESDAY,
            'start_time': '10:00:00',
            'end_time': '19:00:00',
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_response_success(response, status.HTTP_201_CREATED)
        
        # Verify schedule was created
        self.assertEqual(response.data['day_of_week'], DayOfWeek.TUESDAY)
        self.assertEqual(response.data['start_time'], '10:00:00')
        self.assertEqual(str(response.data['campaign']), str(self.campaign.id))

    def test_create_schedule_validation_error(self):
        """Test POST /api/schedules/ - Validation errors."""
        url = f'{self.base_url}/schedules/'
        
        # Test missing required fields
        data = {}
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)
        self.assertIn('campaign', response.data)
        self.assertIn('day_of_week', response.data)
        
        # Test invalid time range (end before start)
        data = {
            'campaign': str(self.campaign.id),
            'day_of_week': DayOfWeek.MONDAY,
            'start_time': '18:00:00',
            'end_time': '09:00:00',  # End before start
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assert_response_error(response)

    def test_retrieve_schedule(self):
        """Test GET /api/schedules/{id}/ - Retrieve specific schedule."""
        url = f'{self.base_url}/schedules/{self.schedule.id}/'
        response = self.client.get(url)
        
        self.assert_response_success(response)
        self.assertEqual(response.data['id'], str(self.schedule.id))
        self.assertEqual(response.data['day_of_week'], DayOfWeek.MONDAY)
        self.assertEqual(str(response.data['campaign']), str(self.campaign.id))

    def test_update_schedule(self):
        """Test PUT /api/schedules/{id}/ - Update schedule."""
        url = f'{self.base_url}/schedules/{self.schedule.id}/'
        data = {
            'campaign': str(self.campaign.id),
            'day_of_week': DayOfWeek.WEDNESDAY,
            'start_time': '08:00:00',
            'end_time': '17:00:00',
            'is_active': False
        }
        
        response = self.client.put(url, data, format='json')
        self.assert_response_success(response)
        
        # Verify updates
        self.assertEqual(response.data['day_of_week'], DayOfWeek.WEDNESDAY)
        self.assertEqual(response.data['start_time'], '08:00:00')
        self.assertEqual(response.data['is_active'], False)

    def test_delete_schedule(self):
        """Test DELETE /api/schedules/{id}/ - Delete schedule."""
        url = f'{self.base_url}/schedules/{self.schedule.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify schedule was deleted
        with self.assertRaises(Schedule.DoesNotExist):
            Schedule.objects.get(id=self.schedule.id)


class IntegrationAPITests(BaseAPITestCase):
    """Test integration scenarios between different entities."""
    
    def test_brand_campaign_integration(self):
        """Test creating campaign for a brand and verifying relationship."""
        # Create a new brand
        brand_data = {
            'name': 'Integration Brand',
            'daily_budget': '200.00',
            'monthly_budget': '5000.00'
        }
        brand_response = self.client.post(f'{self.base_url}/brands/', brand_data, format='json')
        self.assert_response_success(brand_response, status.HTTP_201_CREATED)
        brand_id = brand_response.data['id']
        
        # Create campaign for this brand
        campaign_data = {
            'brand': brand_id,
            'name': 'Integration Campaign',
            'status': CampaignStatus.ACTIVE
        }
        campaign_response = self.client.post(f'{self.base_url}/campaigns/', campaign_data, format='json')
        self.assert_response_success(campaign_response, status.HTTP_201_CREATED)
        campaign_id = campaign_response.data['id']
        
        # Verify campaign is linked to brand
        self.assertEqual(str(campaign_response.data['brand']), brand_id)
        
        # Create spend for this campaign
        spend_data = {
            'campaign': campaign_id,
            'amount': '100.00',
            'spend_date': date.today().isoformat(),
            'spend_type': SpendType.DAILY,
            'description': 'Integration spend'
        }
        spend_response = self.client.post(f'{self.base_url}/spends/', spend_data, format='json')
        self.assert_response_success(spend_response, status.HTTP_201_CREATED)
        
        # Verify spend is linked to campaign
        self.assertEqual(str(spend_response.data['campaign']), campaign_id)
        
        # Create schedule for this campaign
        schedule_data = {
            'campaign': campaign_id,
            'day_of_week': DayOfWeek.FRIDAY,
            'start_time': '09:00:00',
            'end_time': '18:00:00',
            'is_active': True
        }
        schedule_response = self.client.post(f'{self.base_url}/schedules/', schedule_data, format='json')
        self.assert_response_success(schedule_response, status.HTTP_201_CREATED)
        
        # Verify schedule is linked to campaign
        self.assertEqual(str(schedule_response.data['campaign']), campaign_id)

    def test_cascade_operations(self):
        """Test cascade operations when parent entities are deleted."""
        # Create a new brand with campaign
        brand_data = {
            'name': 'Cascade Brand',
            'daily_budget': '100.00',
            'monthly_budget': '1000.00'
        }
        brand_response = self.client.post(f'{self.base_url}/brands/', brand_data, format='json')
        brand_id = brand_response.data['id']
        
        campaign_data = {
            'brand': brand_id,
            'name': 'Cascade Campaign',
            'status': CampaignStatus.ACTIVE
        }
        campaign_response = self.client.post(f'{self.base_url}/campaigns/', campaign_data, format='json')
        campaign_id = campaign_response.data['id']
        
        # Delete the brand
        self.client.delete(f'{self.base_url}/brands/{brand_id}/')
        
        # Verify campaign is also deleted (if cascade is configured)
        campaign_list_response = self.client.get(f'{self.base_url}/campaigns/')
        campaign_ids = [c['id'] for c in campaign_list_response.data]
        self.assertNotIn(campaign_id, campaign_ids)

    def test_filtering_and_search(self):
        """Test filtering and search capabilities."""
        # Create multiple brands with different names
        brands_data = [
            {'name': 'Alpha Brand', 'daily_budget': '100.00', 'monthly_budget': '1000.00'},
            {'name': 'Beta Brand', 'daily_budget': '200.00', 'monthly_budget': '2000.00'},
            {'name': 'Gamma Brand', 'daily_budget': '300.00', 'monthly_budget': '3000.00'}
        ]
        
        for brand_data in brands_data:
            self.client.post(f'{self.base_url}/brands/', brand_data, format='json')
        
        # Test listing all brands
        response = self.client.get(f'{self.base_url}/brands/')
        self.assertGreaterEqual(len(response.data), 4)  # Including the one from setUp
        
        # Test filtering by budget range (if implemented)
        # This would depend on the actual filtering implementation


class ErrorHandlingAPITests(BaseAPITestCase):
    """Test error handling and edge cases."""
    
    def test_invalid_json(self):
        """Test handling of invalid JSON in requests."""
        url = f'{self.base_url}/brands/'
        response = self.client.post(
            url, 
            'invalid json', 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_method_not_allowed(self):
        """Test HTTP methods not allowed."""
        url = f'{self.base_url}/brands/{self.brand.id}/'
        
        # Try PATCH on a resource that doesn't support it (if applicable)
        # This depends on the actual viewset configuration
        
        # Try unsupported methods
        response = self.client.options(url)
        # OPTIONS should be allowed for API discovery
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED])
    
    def test_large_payload(self):
        """Test handling of large payloads."""
        url = f'{self.base_url}/brands/'
        large_name = 'A' * 1000  # Very long name
        
        data = {
            'name': large_name,
            'daily_budget': '100.00',
            'monthly_budget': '1000.00'
        }
        
        response = self.client.post(url, data, format='json')
        # Should either succeed or return validation error, not crash
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])


def run_api_tests():
    """Run all API tests and provide summary."""
    print("🚀 Starting Comprehensive API Test Suite")
    print("=" * 60)
    
    # Import and run Django tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run all tests in this file
    test_suite = TestRunner.build_suite(['test_api_endpoints'])
    result = test_runner.run_suite(test_suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ALL API TESTS PASSED!")
        print("✅ All endpoints are working correctly")
        print("✅ All CRUD operations are functional")
        print("✅ All validations are working")
        print("✅ All integrations are working")
    else:
        print("❌ SOME API TESTS FAILED!")
        print("Please check the test output above for details")
    
    print("\n📊 Test Summary:")
    print(f"   - Tests run: {result.testsRun}")
    print(f"   - Failures: {len(result.failures)}")
    print(f"   - Errors: {len(result.errors)}")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_api_tests()) 
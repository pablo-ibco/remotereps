"""
Django management command to enforce budget limits.
"""

from django.core.management.base import BaseCommand
from spending.services import SpendingService
from typing import Any


class Command(BaseCommand):
    """Management command to enforce budget limits."""
    
    help = 'Enforce budget limits for all active campaigns'
    
    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution."""
        self.stdout.write('Enforcing budget limits...')
        
        spending_service = SpendingService()
        results = spending_service.enforce_budget_limits()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Budget enforcement completed: {results["checked"]} campaigns checked, '
                f'{results["paused_daily"]} paused due to daily budget, '
                f'{results["paused_monthly"]} paused due to monthly budget'
            )
        )
        
        if results['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'{results["errors"]} errors occurred during budget enforcement'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('Budget enforcement operation completed successfully')
        ) 
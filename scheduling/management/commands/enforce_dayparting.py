"""
Django management command to enforce dayparting rules.
"""

from django.core.management.base import BaseCommand
from scheduling.services import SchedulingService
from typing import Any


class Command(BaseCommand):
    """Management command to enforce dayparting rules."""
    
    help = 'Enforce dayparting rules for all campaigns'
    
    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution."""
        self.stdout.write('Enforcing dayparting rules...')
        
        scheduling_service = SchedulingService()
        results = scheduling_service.enforce_dayparting()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Dayparting enforcement completed: {results["activated"]} campaigns activated, '
                f'{results["paused"]} campaigns paused'
            )
        )
        
        if results['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'{results["errors"]} errors occurred during dayparting enforcement'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('Dayparting enforcement operation completed successfully')
        ) 
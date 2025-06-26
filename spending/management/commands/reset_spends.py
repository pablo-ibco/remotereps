"""
Django management command to reset daily and monthly spends.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from spending.services import SpendingService
from typing import Any


class Command(BaseCommand):
    """Management command to reset daily and monthly spends."""
    
    help = 'Reset daily and/or monthly spends for all campaigns'
    
    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            '--daily',
            action='store_true',
            help='Reset daily spends',
        )
        parser.add_argument(
            '--monthly',
            action='store_true',
            help='Reset monthly spends',
        )
        parser.add_argument(
            '--both',
            action='store_true',
            help='Reset both daily and monthly spends',
        )
    
    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution."""
        spending_service = SpendingService()
        
        if not any([options['daily'], options['monthly'], options['both']]):
            raise CommandError(
                'Please specify --daily, --monthly, or --both'
            )
        
        if options['both'] or options['daily']:
            self.stdout.write('Resetting daily spends...')
            daily_results = spending_service.reset_daily_spends()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Daily reset completed: {daily_results["reset"]} campaigns reset, '
                    f'{daily_results["reactivated"]} campaigns reactivated'
                )
            )
            
            if daily_results['errors'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'{daily_results["errors"]} errors occurred during daily reset'
                    )
                )
        
        if options['both'] or options['monthly']:
            self.stdout.write('Resetting monthly spends...')
            monthly_results = spending_service.reset_monthly_spends()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Monthly reset completed: {monthly_results["reset"]} campaigns reset, '
                    f'{monthly_results["reactivated"]} campaigns reactivated'
                )
            )
            
            if monthly_results['errors'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'{monthly_results["errors"]} errors occurred during monthly reset'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('Spend reset operation completed successfully')
        ) 
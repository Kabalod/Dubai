from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup database: create migrations, apply them, and load mock data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up database...')
        
        try:
            with transaction.atomic():
                # Create migrations if needed
                self.stdout.write('Creating migrations...')
                call_command('makemigrations', 'api', verbosity=1)
                
                # Apply migrations
                self.stdout.write('Applying migrations...')
                call_command('migrate', '--run-syncdb', verbosity=1)
                
                # Load mock data
                self.stdout.write('Loading mock data...')
                call_command('load_mock_data', verbosity=1)
                
                self.stdout.write(
                    self.style.SUCCESS('Database setup completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up database: {e}')
            )
            logger.error(f'Error setting up database: {e}')
            raise

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load mock data for Dubai MVP'

    def handle(self, *args, **options):
        self.stdout.write('Loading mock data...')
        
        try:
            with transaction.atomic():
                # Create superuser if not exists
                User = get_user_model()
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@dubai-mvp.com',
                        password='admin123'
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Superuser created: admin/admin123')
                    )
                
                # Create test user
                if not User.objects.filter(username='testuser').exists():
                    User.objects.create_user(
                        username='testuser',
                        email='test@dubai-mvp.com',
                        password='test123'
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Test user created: testuser/test123')
                    )

                # Create DEMO user for frontend
                if not User.objects.filter(email='demo@premium.user').exists():
                    User.objects.create_user(
                        username='demo_premium_user',
                        email='demo@premium.user',
                        password='demo123',
                        first_name='Demo',
                        last_name='Premium'
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Demo user created: demo@premium.user / demo123')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS('Mock data loaded successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading mock data: {e}')
            )
            logger.error(f'Error loading mock data: {e}')
            raise

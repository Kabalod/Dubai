from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.utils import OperationalError
from realty.pfimport.tasks import scrape_property_finder
from datetime import timedelta
from django.utils import timezone
from realty.main.tasks import compute_aggregation_for_caching


class Command(BaseCommand):
    help = "Start all tasks"

    def handle(self, *args, **options):
        now_midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        compute_aggregation_for_caching.using(run_after=now_midnight).enqueue()
        scrape_property_finder.using(
            run_after=now_midnight + timedelta(hours=8)
        ).enqueue()

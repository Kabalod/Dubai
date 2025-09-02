from django.apps import AppConfig
from django.db.utils import OperationalError


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "realty.main"

    def ready(self):
        try:
            from django.utils import timezone
            # from realty.main.tasks import compute_aggregation_for_caching

            now_midnight = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        #   compute_aggregation_for_caching.using(run_after=now_midnight).enqueue()
        except OperationalError:
            """This code run in ci, and since there migth not be any db, we need to ignore this error"""
            pass

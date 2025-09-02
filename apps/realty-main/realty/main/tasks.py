import logging
from datetime import timedelta

from django.utils import timezone
from django_tasks import task

from .models import Area
from .models import Building
from .models import Project
from .stats import calc_and_save_search_log

logger = logging.getLogger(__name__)


@task(priority=-72)
def compute_aggregation_for_caching():
    """
    Task to pre-compute and cache aggregations for all buildings, projects, and areas.
    This helps keep the cache warm and improves performance for users.

    Runs every day at midnight and computes aggregations for:
    1. All Dubai (no search substring)
    2. Each area by name
    3. Each building by name
    4. Each project by name

    The task calculates aggregations for both sales and rental transaction types,
    and for different property components where relevant.
    """
    logger.info("Starting compute_aggregation_for_caching task")
    transaction_types = ["sales", "rental"]
    periods = [
        "1 month",
        "3 months",
        "6 months",
        "1 year",
        "2 years",
    ]

    try:
        # Calculate aggregations for all Dubai (base reference values)
        for transaction_type in transaction_types:
            for period in periods:
                logger.info(
                    f"Computing aggregation for all Dubai: {transaction_type}, {period}"
                )
                calc_and_save_search_log(
                    transaction_type=transaction_type,
                    search_substring=None,
                    property_components=None,
                    period_str=period,
                    return_dict=True,  # We don't need to save to DB
                    use_cache=True,
                )

        # Calculate aggregations for each area
        areas = Area.objects.filter(name_en__isnull=False).exclude(name_en="")
        for area in areas:
            for transaction_type in transaction_types:
                for period in periods:
                    logger.info(
                        f"Computing aggregation for area {area.name_en}: {transaction_type}, {period}"
                    )
                    calc_and_save_search_log(
                        transaction_type=transaction_type,
                        search_substring=area.name_en,
                        property_components=None,
                        period_str=period,
                        return_dict=True,
                        use_cache=True,
                    )

        # Calculate aggregations for each building
        buildings = Building.objects.filter(english_name__isnull=False).exclude(
            english_name=""
        )
        for building in buildings:
            for transaction_type in transaction_types:
                for period in periods:
                    logger.info(
                        f"Computing aggregation for building {building.english_name}: {transaction_type}, {period}"
                    )
                    calc_and_save_search_log(
                        transaction_type=transaction_type,
                        search_substring=building.english_name,
                        property_components=None,
                        period_str=period,
                        return_dict=True,
                        use_cache=True,
                    )

        # Calculate aggregations for each project
        projects = Project.objects.filter(english_name__isnull=False).exclude(
            english_name=""
        )
        for project in projects:
            for transaction_type in transaction_types:
                for period in periods:
                    logger.info(
                        f"Computing aggregation for project {project.english_name}: {transaction_type}, {period}"
                    )
                    calc_and_save_search_log(
                        transaction_type=transaction_type,
                        search_substring=project.english_name,
                        property_components=None,
                        period_str=period,
                        return_dict=True,
                        use_cache=True,
                    )

        logger.info("Completed compute_aggregation_for_caching task")
    except Exception as e:
        logger.error(f"Error in compute_aggregation_for_caching task: {e}")

    # Schedule next run (tomorrow at midnight)
    next_run = timezone.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    compute_aggregation_for_caching.using(run_after=next_run).enqueue()

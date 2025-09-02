import logging
import os
import tempfile
from datetime import timedelta
from pathlib import Path

from django.utils import timezone
from django.core.files import File
from django_tasks import task

from .models import PFJsonUpload

logger = logging.getLogger(__name__)
START_PAGE = 1
END_PAGE = 10


@task()
def scrape_property_finder():
    """
    Daily task to scrape property listings from PropertyFinder.

    Runs every day at 8 AM, scrapes the first 20 pages of property listings,
    processes the data, and imports it into the database system.
    """
    import os
    from django.core.management import call_command

    logger.info("Starting property scraping task")

    # Create a temporary file for the output
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"property_data_{timestamp}.json"

    try:
        # Call our Django management command to scrape properties and generate the JSON file
        # Start from page 1 and scrape 20 pages by default
        logger.info("Running property scraper command")
        call_command("scrape_properties", START_PAGE, END_PAGE, output=output_filename)

        # Load the generated file into the PFJsonUpload model
        # This will trigger the save() method which processes the data
        if os.path.exists(output_filename):
            logger.info(f"Processing scraped data from {output_filename}")
            with open(output_filename, "rb") as file:
                # Create a new PFJsonUpload instance
                upload = PFJsonUpload(
                    # Don't wipe existing data by default
                    wipe_sale_before=False,
                    wipe_rent_before=False,
                    wipe_area_before=False,
                    wipe_buildnig_before=False,
                )
                # Attach the file to the upload_file field
                upload.upload_file.save(
                    f"scheduled_import_{timestamp}.json", File(file)
                )
                # The save method is called automatically and processes the JSON

            # Delete the original file after it's been processed
            logger.info(f"Cleaning up temporary file {output_filename}")
            os.remove(output_filename)
        else:
            logger.error(f"Expected output file {output_filename} not found")

    except Exception as e:
        logger.error(f"Error in property scraping task: {e}", exc_info=True)

    # Schedule next run (tomorrow at 8 AM)
    next_run = timezone.now().replace(
        hour=8, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    scrape_property_finder.using(run_after=next_run).enqueue()

    logger.info(
        "Property scraping task completed, next run scheduled for tomorrow at 8 AM"
    )

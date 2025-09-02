import logging
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from rapidfuzz import fuzz
from rapidfuzz import process
from realty.main.management.projects import get_projects_file
from realty.main.management.utils import download_dubai_pulse_csv
from realty.main.management.utils import safe_str_value
from realty.main.models import Area
from realty.main.models import Building
from realty.main.models import BuildingLiquidityParameterOne
from realty.main.models import Function
from realty.main.models import MergedTransaction
from realty.main.models import Project
from realty.main.models import Room

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populates Projects, Buildings, and MergedTransactions from external Excel/CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--projects-zip",
            type=str,
            default="parsing_dubai_rest.zip",
            help="Path to the dubai rest api projects",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean all objects before populating",
        )

    def handle(self, *args, **options):
        projects_file = get_projects_file(options["projects_zip"])
        transactions_file = get_transactions_file()
        clean = options["clean"]

        if clean:
            logger.info("Cleaning all objects...")
            MergedTransaction.objects.all().delete()
            BuildingLiquidityParameterOne.objects.all().delete()
            Room.objects.all().delete()
            Function.objects.all().delete()
            Building.objects.all().delete()
            Project.objects.all().delete()
            Area.objects.all().delete()
            logger.info("Clean complete.")

        self.populate_projects_and_buildings(projects_file)
        self.populate_transactions(transactions_file)
        logger.info("Population complete.")

    def populate_projects_and_buildings(self, projects_file):
        logger.info("Populating Projects")
        df = pd.read_csv(projects_file)

        for index, row in df.iterrows():
            try:
                json_project_number = format_project_number(
                    row.get("json_project_number")
                )
                json_project_name = safe_str_value(row.get("json_project_name", ""))
                area_name = safe_str_value(row.get("area", ""))
                total_units = row.get("total_units", 0) or 0
                room_types = safe_str_value(row.get("room_types", ""))
                floors = row.get("floors", 0) or 0
                matched_num_value = row.get("matched_project_number", None)
                # matched_project_number = format_project_number(matched_num_value)

                json_building_name = safe_str_value(row.get("json_building_name", ""))
                if not json_building_name:
                    json_building_name = json_project_name

                area_obj, _ = Area.objects.get_or_create(name_en=area_name)

                project, _ = Project.objects.get_or_create(
                    project_number=json_project_number,
                    defaults={
                        "english_name": json_project_name,
                        "total_units": total_units,
                    },
                )

                # if matched_project_number:
                #     project = Project.objects.filter(
                #         project_number=matched_project_number
                #     ).first()
                #     if not project:
                #         logger.info(
                #             f"No project with number {matched_project_number}. Creating new."
                #         )
                #         project =
                # else:
                #     project = Project.objects.create(
                #         project_number=json_project_number,
                #         english_name=json_project_name,
                #         total_units=total_units,
                #     )

                # existing_buildings = Building.objects.filter(project=project)
                # if existing_buildings.exists():
                #     first_word = (
                #         project.english_name.split()[0]
                #         if project.english_name.split()
                #         else project.english_name
                #     )
                #     masked_name = (
                #         f"{json_building_name} (<i>in project: {first_word}</i>)"
                #     )
                #     for b in existing_buildings:
                #         if "(<i>in project:" not in b.english_name:
                #             b.english_name = (
                #                 f"{b.english_name} (<i>in project: {first_word}</i>)"
                #             )
                #             b.save()
                # else:
                #     masked_name = json_building_name
                # first_word = (
                #             project.english_name.split()[0]
                #             if project.english_name.split()
                #             else project.english_name
                #         )
                # masked_name = f"{json_building_name} (project: {first_word})"
                masked_name = json_building_name
                b_qs = Building.objects.filter(
                    project=project, english_name__iexact=masked_name
                )
                if b_qs.exists():
                    building = b_qs.first()
                    building.floor_count = floors
                    building.total_units = total_units
                    building.area = area_obj
                    building.english_name = masked_name
                    building.save()
                else:
                    building = Building.objects.create(
                        project=project,
                        english_name=masked_name,
                        floor_count=floors,
                        total_units=total_units,
                        area=area_obj,
                    )

                building.building_count = building.project.buildings.count()
                building.save()

                if room_types:
                    project.functions.all().delete()
                    func = Function.objects.create(
                        project=project, english_name="Rooms"
                    )
                    parts = [p.strip() for p in room_types.split(";") if p.strip()]
                    for part in parts:
                        if "(" in part and part.endswith(")"):
                            rtype = part.split("(")[0].strip()
                            value = part.split("(")[1].rstrip(")")
                            Room.objects.create(
                                function=func,
                                english_name=rtype,
                                value=value,
                                building=building,
                            )

            except Exception as e:
                logger.error(f"Error in row {index}: {e}")

        logger.info("Projects and buildings populated.")

    def populate_transactions(self, transactions_file):
        df = pd.read_csv(transactions_file)
        process_transaction_chunk(df)
        # total_rows = len(df)
        # num_processes = max(multiprocessing.cpu_count(), 4)
        # chunks = np.array_split(df, num_processes)
        # logger.info(
        #     f"Processing {total_rows} transactions with {num_processes} processes"
        # )
        # total_processed = 0
        # total_errors = 0
        # with ProcessPoolExecutor(max_workers=num_processes) as executor:
        #     results = list(executor.map(process_transaction_chunk, chunks))
        #     for processed, errors in results:
        #         total_processed += processed
        #         total_errors += errors
        # for chunk in chunks:
        #     process_transaction_chunk.enqueue(chunk)
        # tasks = []
        # with tempfile.TemporaryDirectory() as temp_dir:
        #     # Save each chunk to a temporary file
        #     for i, chunk in enumerate(chunks):
        #         chunk_file = os.path.join(temp_dir, f"chunk_{i}.csv")
        #         chunk.to_csv(chunk_file, index=False)
        #         # Enqueue the file path instead of the DataFrame
        #         tasks.append(process_transaction_chunk.enqueue(chunk_file))
        #
        #         total_processed = 0
        #         total_errors = 0
        #         remaining_tasks = tasks.copy()
        #
        #         while remaining_tasks:
        #             for i in range(
        #                 len(remaining_tasks) - 1, -1, -1
        #             ):  # Iterate backwards for safe removal
        #                 task = remaining_tasks[i]
        #                 task.refresh()
        #                 if task.status == ResultStatus.SUCCEEDED:
        #                     # Extract results from completed task
        #                     if task.return_value:
        #                         processed, errors = task.return_value
        #                         total_processed += processed
        #                         total_errors += errors
        #                         logger.info(
        #                             f"Task completed: processed={processed}, errors={errors}"
        #                         )
        #                     else:
        #                         logger.warning("Task completed but returned no value")
        #                     # Remove from pending tasks
        #                     remaining_tasks.pop(i)
        #                 elif task.status == ResultStatus.FAILED:
        #                     logger.error(f"Task failed with status {task.status}")
        #                     remaining_tasks.pop(i)
        #
        #             # If we still have tasks, wait before checking again
        #             if remaining_tasks:
        #                 logger.info(
        #                     f"Waiting for {len(remaining_tasks)} tasks to complete..."
        #                 )
        #                 time.sleep(5)
        #
        #     logger.info(
        #         f"All transaction tasks completed: {total_processed} processed, {total_errors} errors"
        #     )

        logger.info("Transactions populated.")


# @task()
def process_transaction_chunk(chunk_df):
    import pandas as pd

    # from django import db
    # db.connections.close_all()
    # import os
    #
    # print("Processing chunk ", randint(0, 1000))
    # print(os.getpid())
    #
    # logger.info(f"Processing chunk file: {chunk_file}")
    # chunk_df = pd.read_csv(chunk_file)
    # processed, errors = 0, 0
    for index, row in chunk_df.iterrows():
        try:
            instance_date_str = safe_str_value(row.get("instance_date", ""))
            try:
                instance_date = pd.to_datetime(instance_date_str)
            except Exception:
                instance_date = timezone.now()

            transaction_number = safe_str_value(row.get("transaction_id", ""))
            trans_group_en = safe_str_value(row.get("trans_group_en", ""))
            procedure_en = safe_str_value(row.get("procedure_name_en", ""))
            area_en = safe_str_value(row.get("area_name_en", ""))
            building_name_en = safe_str_value(row.get("building_name_en", ""))
            master_project_en = safe_str_value(row.get("master_project_en", ""))
            rooms_en = safe_str_value(row.get("rooms_en", ""))

            actual_worth = row.get("actual_worth", 0)
            if pd.isna(actual_worth):
                actual_worth = 0

            procedure_area = row.get("procedure_area", 0)
            if pd.isna(procedure_area):
                procedure_area = 0

            if "Mortgage" in trans_group_en:
                transaction_type = "sales"
            else:
                transaction_type = "rental"

            deal_year = instance_date.year
            deal_month = instance_date.month

            area_obj, _ = Area.objects.get_or_create(name_en=area_en)

            building = find_building_exact_or_fuzzy(building_name_en)
            if not building:
                logger.warning(
                    f"Transaction {transaction_number}: building '{building_name_en}' not found. Skipping."
                )
                continue

            price_value = float(actual_worth) if actual_worth else 0
            area_value = float(procedure_area) if procedure_area else 0

            meter_price = 0
            if price_value > 0 and area_value > 0:
                meter_price = price_value / area_value

            building_rooms_count = 0
            if building.project.buildings.count() == 1:
                building_rooms_count = building.project.total_units or 0

            same_room_type_in_building = (
                building.rooms.filter(english_name=rooms_en).only("value").first()
            )
            if same_room_type_in_building:
                same_rooms_count_in_building = same_room_type_in_building.value
            else:
                same_rooms_count_in_building = None
            MergedTransaction.objects.create(
                transaction_type=transaction_type,
                building=building,
                date_of_transaction=instance_date.date(),
                building_name=building_name_en,
                location_name=area_en,
                number_of_rooms=rooms_en,
                sqm=area_value,
                transaction_price=price_value,
                detail_link="",
                something_important_v1=master_project_en,
                period=procedure_en,
                meter_sale_price=meter_price,
                deal_year=deal_year,
                area=area_obj,
                same_rooms_count_in_building=same_rooms_count_in_building,
                building_rooms_count=building_rooms_count,
            )

            if transaction_type == "sales":
                liq_obj, _ = BuildingLiquidityParameterOne.objects.get_or_create(
                    building=building,
                    year=deal_year,
                    month=deal_month,
                )
                liq_obj.liquidity_parameter_one += 1
                liq_obj.save()
        except Exception as e:
            logger.error(f"Error in transaction row {index}: {e}")


def get_transactions_file() -> Path:
    transactions_file = download_dubai_pulse_csv(
        site_url="https://www.dubaipulse.gov.ae/data/dld-transactions/dld_transactions-open",
        file_type="transactions",
    )
    logger.info(f"Reading file {transactions_file} into DataFrame")
    df = pd.read_csv(transactions_file)
    logger.info("Filtering transactions to keep only 'Flat'")
    filtered_df = df[df["property_sub_type_en"] == "Flat"].copy()
    filtered_file_name = (
        transactions_file.parent / f"{transactions_file.stem}_filtered.csv"
    )
    filtered_df.to_csv(filtered_file_name, index=False)
    logger.info(f"Wrote filtered file {filtered_file_name}")
    return filtered_file_name


def normalize_str(s: str) -> str:
    if not s:
        return ""
    return s.strip().lower()


def format_project_number(value):
    if value is None:
        return ""

    try:
        num = float(value)
        if num.is_integer():
            return str(int(num))
        return str(num)
    except (ValueError, TypeError):
        return ""


def find_building_exact_or_fuzzy(name_str, threshold=80):
    if not name_str:
        return None
    exact_qs = Building.objects.filter(english_name__iexact=name_str)
    count_exact = exact_qs.count()
    if count_exact == 1:
        return exact_qs.first()
    elif count_exact > 1:
        logger.warning(f"Multiple buildings found for '{name_str}'. Using first.")
        return exact_qs.first()
    else:
        buildings = Building.objects.all()
        names = [b.english_name for b in buildings if b.english_name]
        search_norm = normalize_str(name_str)
        result = process.extractOne(search_norm, names, scorer=fuzz.WRatio)
        if result:
            best_match, score, _ = result
            if score >= threshold:
                fuzzy_qs = Building.objects.filter(english_name__iexact=best_match)
                if fuzzy_qs.count() == 1:
                    logger.info(
                        f"Fuzzy match: '{name_str}' => '{best_match}' (score: {score})"
                    )
                    return fuzzy_qs.first()
                elif fuzzy_qs.count() > 1:
                    logger.warning(
                        f"Fuzzy match found multiple for '{best_match}'. Using first."
                    )
                    return fuzzy_qs.first()
        logger.warning(f"Building '{name_str}' not found.")
        return None

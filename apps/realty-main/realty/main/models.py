# realty/main/models.py:
import logging
import os
from pathlib import Path

from django.core.management import call_command
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE
from django_lifecycle import hook
from django_lifecycle import LifecycleModel
from django_tasks import task


import tempfile
import requests


logger = logging.getLogger(__name__)
# realty/main/models.py


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


class MasterProject(BaseModel):
    english_name = models.CharField(max_length=255, unique=True, db_index=True)
    arabic_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.english_name


class Developer(BaseModel):
    number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    english_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    arabic_name = models.CharField(max_length=255, blank=True, null=True)
    developer_id = models.IntegerField(
        unique=True, db_index=True, blank=True, null=True
    )
    is_followed = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"[{self.developer_id or self.number}] {self.english_name or ''}"


class Project(BaseModel):
    project_number = models.CharField(
        max_length=50, blank=True, null=True, db_index=True
    )
    english_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    arabic_name = models.CharField(max_length=255, blank=True, null=True)
    worth = models.FloatField(blank=True, null=True)
    total_area = models.FloatField(blank=True, null=True)
    total_units = models.PositiveIntegerField(blank=True, null=True)
    developer = models.ForeignKey(
        Developer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects_as_developer",
    )
    main_developer = models.ForeignKey(
        Developer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects_as_main_developer",
    )
    status_en = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    is_followed = models.BooleanField(default=False, db_index=True)
    facilities = models.JSONField(blank=True, null=True)
    master_project = models.ForeignKey(
        MasterProject,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )

    def __str__(self):
        return f"Project {self.project_number} - {self.english_name or ''}"


class Area(models.Model):
    area_idx = models.IntegerField(db_index=True, blank=True, null=True)
    name_ar = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    name_en = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    def __str__(self):
        return self.name_en if self.name_en else "Unnamed"


class Location(BaseModel):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="location"
    )
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)


class Land(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="lands")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    english_name = models.CharField(max_length=255, blank=True, null=True)
    arabic_name = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    property_type = models.CharField(max_length=50, blank=True, null=True)
    floor_count = models.IntegerField(blank=True, null=True)


class Building(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="buildings"
    )
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    english_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    arabic_name = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    property_type = models.CharField(
        max_length=50, blank=True, null=True, db_index=True
    )
    floor_count = models.IntegerField(blank=True, null=True)
    total_units = models.PositiveIntegerField(blank=True, null=True)
    building_count = models.PositiveIntegerField(
        blank=True, null=True, help_text="Number of buildings in the project"
    )
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, blank=True, null=True, db_index=True
    )
    area_by_pf = models.ForeignKey(
        "pfimport.Area",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
    )

    def __str__(self):
        first_word = (
            self.project.english_name.split()[0]
            if self.project.english_name and self.project.english_name.split()
            else self.project.english_name
        )
        return f"{self.english_name} (project: {first_word})"

    def number_of_rooms(self):
        """
        Возвращает значение number_of_rooms
        из первой MergedTransaction для этого Building.
        """
        first_tx = (
            MergedTransaction.objects.filter(building=self).order_by("pk").first()
        )
        return first_tx.number_of_rooms if first_tx else None


class Function(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="functions"
    )
    english_name = models.CharField(max_length=255, blank=True, null=True)
    arabic_name = models.CharField(max_length=255, blank=True, null=True)


class Room(BaseModel):
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, blank=True, null=True, related_name="rooms"
    )
    function = models.ForeignKey(
        Function, on_delete=models.CASCADE, related_name="rooms"
    )
    english_name = models.CharField(max_length=255, blank=True, null=True)
    arabic_name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=50, blank=True, null=True)


class BuildingLiquidityParameterOne(models.Model):
    """
    Stores how many 'sales' transactions happened in a specific building for each year/month.
    """

    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="liquidity_stats"
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    liquidity_parameter_one = models.PositiveIntegerField(
        default=0, help_text="Number of sales in this month"
    )

    class Meta:
        unique_together = ("building", "year", "month")

    def __str__(self):
        return f"{self.building} | {self.year}-{self.month} => {self.liquidity_parameter_one}"


class MergedTransaction(BaseModel):
    TRANSACTION_CHOICES = [
        ("sales", "Sales"),
        ("rental", "Rental"),
    ]
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_CHOICES, db_index=True
    )
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    date_of_transaction = models.DateField(default=timezone.now, db_index=True)
    building_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    location_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    number_of_rooms = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    sqm = models.FloatField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Area in sq.ft. (if missing, set 0)",
    )
    roi = models.FloatField(blank=True, null=True, db_index=True)
    transaction_price = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True, db_index=True
    )
    detail_link = models.URLField(blank=True, null=True, db_index=True)
    something_important_v1 = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    period = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    meter_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True, db_index=True
    )
    deal_year = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, blank=True, null=True, db_index=True
    )
    same_rooms_count_in_building = models.PositiveIntegerField(
        blank=True, null=True, default=12
    )
    building_rooms_count = models.PositiveIntegerField(blank=True, null=True, default=0)

    master_project = models.ForeignKey(
        MasterProject,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rental_transactions",
    )

    class Meta:
        indexes = [
            models.Index(fields=["transaction_price", "sqm"]),
            models.Index(fields=["meter_sale_price", "deal_year"]),
        ]

    @property
    def property_components(self):
        return self.number_of_rooms

    @property_components.setter
    def property_components(self, value):
        self.number_of_rooms = value

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.building_name} [{self.date_of_transaction}]"


class MergedRentalTransaction(BaseModel):
    transaction_type = models.CharField(
        max_length=10, default="rental", editable=False, db_index=True
    )
    # Связи
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, blank=True, null=True, db_index=True
    )

    date_of_transaction = models.DateField(default=timezone.now, db_index=True)
    building_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    location_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    number_of_rooms = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    sqm = models.FloatField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Area in sq.ft. (if missing, set 0)",
    )

    transaction_price = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True, db_index=True
    )
    detail_link = models.URLField(blank=True, null=True, db_index=True)
    something_important_v1 = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    # same_rooms_count_in_building = models.PositiveIntegerField(
    #     blank=True, null=True, default=1
    # )
    # building_rooms_count = models.PositiveIntegerField(
    #     blank=True, null=True, default=1
    # )

    # MORE than 90% we will delete after debag

    contract_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    contract_reg_type_id = models.CharField(max_length=50, blank=True, null=True)
    contract_reg_type_ar = models.CharField(max_length=255, blank=True, null=True)
    contract_reg_type_en = models.CharField(max_length=255, blank=True, null=True)

    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)

    # contract_amount = models.FloatField(blank=True, null=True)
    annual_amount = models.FloatField(blank=True, null=True)

    no_of_prop = models.IntegerField(blank=True, null=True)
    line_number = models.IntegerField(blank=True, null=True)

    is_free_hold = models.BooleanField(default=False)

    ejari_bus_property_type_id = models.CharField(max_length=50, blank=True, null=True)
    ejari_bus_property_type_ar = models.CharField(max_length=255, blank=True, null=True)
    ejari_bus_property_type_en = models.CharField(max_length=255, blank=True, null=True)

    ejari_property_type_id = models.CharField(max_length=50, blank=True, null=True)
    ejari_property_type_en = models.CharField(max_length=255, blank=True, null=True)
    ejari_property_type_ar = models.CharField(max_length=255, blank=True, null=True)

    ejari_property_sub_type_id = models.CharField(max_length=50, blank=True, null=True)
    ejari_property_sub_type_en = models.CharField(max_length=255, blank=True, null=True)
    ejari_property_sub_type_ar = models.CharField(max_length=255, blank=True, null=True)

    property_usage_en = models.CharField(max_length=255, blank=True, null=True)
    property_usage_ar = models.CharField(max_length=255, blank=True, null=True)

    project_number = models.CharField(max_length=50, blank=True, null=True)
    project_name_ar = models.CharField(max_length=255, blank=True, null=True)
    project_name_en = models.CharField(max_length=255, blank=True, null=True)

    master_project_ar = models.CharField(max_length=255, blank=True, null=True)
    master_project_en = models.CharField(max_length=255, blank=True, null=True)

    area_id_csv = models.IntegerField(blank=True, null=True)
    area_name_ar = models.CharField(max_length=255, blank=True, null=True)
    area_name_en = models.CharField(max_length=255, blank=True, null=True)

    actual_area = models.FloatField(blank=True, null=True)

    nearest_landmark_ar = models.CharField(max_length=255, blank=True, null=True)
    nearest_landmark_en = models.CharField(max_length=255, blank=True, null=True)
    nearest_metro_ar = models.CharField(max_length=255, blank=True, null=True)
    nearest_metro_en = models.CharField(max_length=255, blank=True, null=True)
    nearest_mall_ar = models.CharField(max_length=255, blank=True, null=True)
    nearest_mall_en = models.CharField(max_length=255, blank=True, null=True)

    tenant_type_id = models.IntegerField(blank=True, null=True)
    tenant_type_ar = models.CharField(max_length=255, blank=True, null=True)
    tenant_type_en = models.CharField(max_length=255, blank=True, null=True)

    # Если хотите, оставьте period (как у вас уже было),
    # или любые другие поля, индексы и т. д.
    period = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    meter_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )

    @property
    def same_rooms_count_in_building(self):
        """
        Возвращает значение same_rooms_count_in_building
        из первой MergedTransaction того же building.
        """
        if not self.building_id:
            return 1
        first_tx = MergedTransaction.objects.filter(building=self.building).first()
        return first_tx.same_rooms_count_in_building if first_tx else 0

    @property
    def building_rooms_count(self):
        """
        Возвращает значение building_rooms_count
        из первой MergedTransaction того же building.
        """
        if not self.building_id:
            return 1
        first_tx = MergedTransaction.objects.filter(building=self.building).first()
        return first_tx.building_rooms_count if first_tx else 0

    class Meta:
        # Если у вас есть уже некий индекс на transaction_price, sqm — оставьте или удалите
        indexes = [
            models.Index(fields=["period"]),
            # можно добавить уникальный индекс, если нужно (contract_id, date_of_transaction)
            # но тогда надо убедиться, что не будет дубликатов.
        ]

    def __str__(self):
        return f"Rental {self.contract_id} [{self.date_of_transaction}]"


# --- Импорт данных и служебные модели ---


class CsvImport(LifecycleModel):
    """
    Импорт данных из двух CSV-файлов, задаваемых URL-ами.
    Создаётся из админки → сразу уходит в фоновую задачу.
    """

    giper_csv_url = models.URLField("URL giper_matched_output.csv")
    transactions_csv_url = models.URLField("URL tr_*.csv (большой)")
    chunk_size = models.PositiveIntegerField(default=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    STATUS_CHOICES = [
        ("created", "Created"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="created")
    log = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"CSV import #{self.pk} ({self.status})"

    # ---------------- lifecycle ---------------- #
    @hook(AFTER_CREATE)
    def enqueue_task(self):
        run_csv_import.enqueue(self.pk)


@task()
def run_csv_import(import_id: int):
    """
    Качаем CSV-ки, запускаем populate_db_2, чистим за собой.
    Файл удаляем В ЛЮБОМ случае (try/finally).
    """
    from django.utils import timezone

    imp = CsvImport.objects.get(pk=import_id)

    if imp.status not in {"created", "failed"}:
        logger.warning("Import %s already running/finished", import_id)
        return

    imp.status = "running"
    imp.started_at = timezone.now()
    imp.log = ""
    imp.save()

    def _download(url: str) -> Path:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(r.content)
        tmp.close()
        return Path(tmp.name)

    tmp_giper = tmp_tr = None
    try:
        imp.log += "Downloading files...\n"
        tmp_giper = _download(imp.giper_csv_url)
        tmp_tr = _download(imp.transactions_csv_url)

        cmd_args = [
            "populate_db_2",
            f"--giper_csv={tmp_giper}",
            f"--transactions_csv={tmp_tr}",
            f"--chunk-size={imp.chunk_size}",
        ]
        imp.log += f"Calling: python manage.py {' '.join(cmd_args)}\n"
        call_command(*cmd_args)

        imp.status = "completed"
        imp.log += "Import finished successfully.\n"
    except Exception as exc:  # noqa: BLE001
        imp.status = "failed"
        imp.log += f"ERROR: {exc}\n"
        logger.exception("CSV import %s failed", import_id)
    finally:
        for p in (tmp_giper, tmp_tr):
            if p and p.exists():
                p.unlink(missing_ok=True)
        imp.finished_at = timezone.now()
        imp.save()


@task()
def run_csv_rent_import(import_id: int):
    """
    Скачивает CSV аренды, вызывает populate_db_rents,
    потом чистит временный файл.
    """
    from realty.main.models import (
        CsvRentImport,
    )  # локальный импорт, чтобы избежать круговых
    import logging, os, gc

    logger = logging.getLogger(__name__)

    imp = CsvRentImport.objects.get(pk=import_id)
    if imp.status not in {"created", "failed"}:
        return

    imp.status, imp.started_at, imp.log = "running", timezone.now(), ""
    imp.save(update_fields=("status", "started_at", "log"))

    def _download(url: str) -> Path:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(r.content)
        tmp.close()
        return Path(tmp.name)

    tmp_file = None
    try:
        imp.log += "Downloading rent CSV…\n"
        tmp_file = _download(imp.rents_csv_url)

        cmd = [
            "populate_db_rents",
            str(tmp_file),
            f"--start-line={imp.start_line}",
            "--clean-first",
        ]
        imp.log += f"Calling: python manage.py {' '.join(cmd)}\n"
        call_command(*cmd)

        imp.status, msg = "completed", "Import finished successfully.\n"
    except Exception as exc:  # noqa: BLE001
        imp.status, msg = "failed", f"ERROR: {exc}\n"
        logging.exception("Rent import %s failed", import_id)
    finally:
        if tmp_file and tmp_file.exists():
            tmp_file.unlink(missing_ok=True)
        imp.finished_at, imp.log = timezone.now(), imp.log + msg
        imp.save()
        gc.collect()  # на всякий случай


# ── модель ────────────────────────────────────────────────────────
class CsvRentImport(LifecycleModel):
    """
    Импорт аренды (populate_db_rents). Запускается автоматически после сохранения.
    """

    rents_csv_url = models.URLField("URL CSV-файла аренды")
    start_line = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    STATUS = [
        ("created", "Created"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=12, choices=STATUS, default="created")
    log = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Rent import #{self.pk} ({self.status})"

    @hook(AFTER_CREATE)
    def enqueue_task(self):
        run_csv_rent_import.enqueue(self.pk)


class DataImport(LifecycleModel):
    STATUS_CHOICES = [
        ("created", _("Created")),
        ("on_going", _("On Going")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
        ("cancelled", _("Cancelled")),
    ]

    projects_zipfile = models.FileField(help_text=_("Project zip file"), blank=True)
    clean_data = models.BooleanField(
        default=False, help_text=_("Clean all objects before populating")
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import {self.id} ({self.status})"

    @hook(AFTER_CREATE)
    def run_import_task(self):
        run_import.enqueue(self.pk)


@task()
def run_import(data_import_id):
    """Execute the import process"""
    logger.info(f"Running import {data_import_id}")
    try:
        data_import = DataImport.objects.get(id=data_import_id)
    except DataImport.DoesNotExist:
        logger.error(f"Data import {data_import_id} does not exist")
        return
    if Path("data_import.lock").exists():
        logger.error("Data import already on going")
        data_import.status = "cancelled"
        return
    lock = Path("data_import.lock")
    lock.touch()
    lock.write_text(str(os.getpid()))
    try:
        data_import.status = "on_going"
        data_import.save()
        if data_import.projects_zipfile:
            call_command(
                "populate_db",
                projects_zip=data_import.projects_zipfile,
                clean=data_import.clean_data,
            )
        else:
            call_command("populate_db", clean=data_import.clean_data)
        data_import.status = "completed"
    except Exception as e:
        data_import.status = "failed"
        data_import.error_message = str(e)
    finally:
        lock.unlink(missing_ok=True)
        data_import.save()


class SearchTransactionsLog(models.Model):
    """
    Stores each call to `searchTransactions` and aggregated metrics.
    """

    requested_at = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=20, blank=True, null=True)
    search_substring = models.CharField(max_length=255, blank=True, null=True)
    property_components = models.JSONField(default=list, blank=True, null=True)
    period = models.CharField(max_length=50, blank=True, null=True)
    avg_price = models.FloatField(blank=True, null=True)
    transaction_count = models.PositiveIntegerField(blank=True, null=True)
    transaction_count_change_percent = models.FloatField(blank=True, null=True)
    median_price = models.FloatField(blank=True, null=True)
    median_price_change_percent = models.FloatField(blank=True, null=True)
    avg_price_per_sqft = models.FloatField(blank=True, null=True)
    building_count = models.PositiveIntegerField(blank=True, null=True)
    total_units = models.PositiveIntegerField(blank=True, null=True)
    price_range = models.CharField(max_length=100, blank=True, null=True)
    special_liquidity_calc = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"SearchLog {self.id} at {self.requested_at}"

# -------------------------------- pfimport/models.py --------------------------------
import datetime, json, logging, shlex, tempfile, gc
from decimal import Decimal
from io import StringIO
from pathlib import Path

import requests
from django.core.files.base import File
from django.core.management import call_command
from django.db import models
from django.utils import timezone
from django_tasks import task
from django_lifecycle import LifecycleModel, AFTER_CREATE, AFTER_SAVE, hook

from realty.main.models import Building as DldBuilding

# Added this constant with all allowed areas
AREAS_WITH_PROPERTY = {
    "Jumeirah Village Circle": 0,
    "Business Bay": 0,
    "Dubai Land": 0,
    "Downtown Dubai": 0,
    "Dubai Marina": 0,
    "Mohammed Bin Rashid City": 0,
    "Jumeirah Village Triangle": 0,
    "Deira": 0,
    "Arjan": 0,
    "Dubai Creek Harbour The Lagoons": 0,
    "Dubai Hills Estate": 0,
    "Al Furjan": 0,
    "Dubai Science Park": 0,
    "Dubai Sports City": 0,
    "Al Jaddaf": 0,
    "Palm Jumeirah": 0,
    "Dubai Harbour": 0,
    "Jumeirah Lake Towers": 0,
    "City of Arabia": 0,
    "Dubai Production City IMPZ": 0,
    "Dubai Land Residence Complex": 0,
    "Dubai South Dubai World Central": 0,
    "Dubai Investment Park DIP": 0,
    "Maritime City": 0,
    "Meydan": 0,
    "Dubai Studio City": 0,
    "Dubai Silicon Oasis": 0,
    "Al Satwa": 0,
    "Motor City": 0,
    "Jumeirah Beach Residence": 0,
    "DAMAC Hills": 0,
    "Town Square": 0,
    "Bukadra": 0,
    "Al Warsan": 0,
    "Wasl Gate": 0,
    "City Walk": 0,
    "Zabeel": 0,
    "Umm Suqeim": 0,
    "Al Wasl": 0,
    "International City": 0,
    "Mina Rashid": 0,
    "Jebel Ali": 0,
    "Expo City": 0,
    "Damac Lagoons": 0,
    "Bluewaters": 0,
    "DIFC": 0,
    "Downtown Jebel Ali": 0,
    "Jumeirah": 0,
    "Damac Hills": 0,
    "Discovery Gardens": 0,
    "Sheikh Zayed Road": 0,
    "Al Barsha": 0,
    "Nad Al Sheba": 0,
    "Ras Al Khor": 0,
    "Barsha Heights Tecom": 0,
    "Culture Village": 0,
    "Greens": 0,
    "Old Town": 0,
    "Mirdif": 0,
    "The Views": 0,
    "Dubai Design District": 0,
    "Al Sufouh": 0,
    "Dubai Industrial City": 0,
    "Jumeirah Islands": 0,
    "Living Legends": 0,
    "Dubai Media City": 0,
    "Al Safa": 0,
    "Dubai Internet City": 0,
    "Emirates Hills": 0,
    "The World Islands": 0,
    "Jumeirah Golf Estates": 0,
    "Falcon City of Wonders": 0,
    "Al Quoz": 0,
    "Dubai Festival City": 0,
    "The Hills": 0,
    "Al Muhaisnah": 0,
    "Al Yelayiss": 0,
    "Al Barari": 0,
    "Bur Dubai": 0,
    "World Trade Center": 0,
    "Mudon": 0,
    "The Valley": 0,
    "Wadi Al Safa": 0,
    "Dubai Waterfront": 0,
    "DuBiotech": 0,
    "The Oasis by Emaar": 0,
    "Nadd Al Hammar": 0,
    "Al Qusais": 0,
    "Arabian Ranches": 0,
    "Wadi Al Safa": 0,
    "Palm Jebel Ali": 0,
    "Al Nahda": 0,
    "Tilal Al Ghaf": 0,
    "Mohammad Bin Rashid Gardens": 0,
}

logger = logging.getLogger(__name__)


def _clean_str(val: str | None) -> str | None:
    """Убираем NUL (\x00) и невидимые управляющие символы."""
    if not val:
        return None
    # сначала превращаем всё в str (на всякий случай Decimal и пр.)
    s = str(val)
    # убираем \x00 и остальные C0-control chars (0x00-0x1F), кроме \t \n \r
    return "".join(
        ch for ch in s if ch not in ("\x00",) and (ch >= "\x20" or ch in "\t\n\r")
    )


# ────────────────────── 1. ЗАДАЧА ДЛЯ ЛЮБЫХ management-КОМАНД ─────────────────────
@task()
def run_management_job(job_id: int) -> None:
    """Выполняет management-команду, указанную в CommandJob.command."""
    from .models import CommandJob  # локальный импорт, чтобы не ловить циклы

    job = CommandJob.objects.get(pk=job_id)

    if job.status == "running":  # уже идёт
        logger.warning("CommandJob %s already running", job_id)
        return

    job.status, job.started_at, job.log = "running", timezone.now(), ""
    job.save(update_fields=("status", "started_at", "log"))

    parts = shlex.split(job.command.strip())
    if not parts:
        job.status = "failed"
        job.finished_at = timezone.now()
        job.log = "Empty command\n"
        job.save()
        return

    out, exc_msg = StringIO(), None
    try:
        call_command(*parts, stdout=out)
        job.status = "completed"
    except SystemExit as e:
        job.status, exc_msg = "failed", f"SystemExit: {e.code}\n"
        logger.exception("CommandJob %s raised SystemExit", job_id)
    except Exception as exc:  # noqa: BLE001
        job.status, exc_msg = "failed", f"{type(exc).__name__}: {exc}\n"
        logger.exception("CommandJob %s failed", job_id)

    job.finished_at = timezone.now()
    job.log += out.getvalue() + (exc_msg or "")
    job.save()
    gc.collect()


# ───────────────────────────── 2. МОДЕЛЬ CommandJob ───────────────────────────
class CommandJob(LifecycleModel):
    """
    Хранит одну management-команду.
    После создания или изменения `command` ставит задачу run_management_job.
    """

    command = models.CharField(
        max_length=255,
        help_text='Не пишите "python manage.py" – только саму команду и её аргументы.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    STATUS = [
        ("created", "Created"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    status = models.CharField(max_length=10, choices=STATUS, default="created")
    log = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Job #{self.pk}: {self.command[:40]}… ({self.status})"

    # автозапуск после создания
    @hook(AFTER_CREATE)
    def _enqueue_on_create(self):
        run_management_job.enqueue(self.pk)

    # автозапуск ТОЛЬКО если изменилось поле command
    @hook(AFTER_SAVE)
    def _enqueue_on_change(self):
        if self.has_changed("command") and self.status != "running":
            run_management_job.enqueue(self.pk)


# ────────────────────── 3. ЗАДАЧА И МОДЕЛЬ ДЛЯ PF-JSON ИМПОРТА ────────────────
@task()
def run_pfjson_import(job_id: int):
    """Скачивает JSON по URL, создаёт PFJsonUpload, удаляет tmp-файл."""
    from .models import PFJsonImport, PFJsonUpload

    job = PFJsonImport.objects.get(pk=job_id)

    if job.status not in {"created", "failed"}:
        return

    job.status, job.started_at, job.log = "running", timezone.now(), ""
    job.save(update_fields=("status", "started_at", "log"))

    def _download(url: str) -> Path:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.write(r.content)
        tmp.close()
        return Path(tmp.name)

    tmp_path, tail = None, ""
    try:
        job.log += "Downloading JSON…\n"
        tmp_path = _download(job.json_url)

        with tmp_path.open("rb") as f:
            PFJsonUpload(
                wipe_sale_before=job.wipe_sale_before,
                wipe_rent_before=job.wipe_rent_before,
                wipe_area_before=job.wipe_area_before,
                wipe_buildnig_before=job.wipe_buildnig_before,
            ).upload_file.save(tmp_path.name, File(f), save=True)

        job.status, tail = "completed", "Import finished successfully.\n"
    except Exception as exc:  # noqa: BLE001
        job.status, tail = "failed", f"ERROR: {exc}\n"
        logger.exception("PF JSON import %s failed", job_id)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        job.finished_at, job.log = timezone.now(), job.log + tail
        job.save()
        gc.collect()


class PFJsonImport(LifecycleModel):
    """
    Заводится из админки: хранит URL JSON-файла и флаги очистки.
    После сохранения ставит run_pfjson_import.
    """

    json_url = models.URLField("URL JSON-файла")
    wipe_sale_before = models.BooleanField(default=False)
    wipe_rent_before = models.BooleanField(default=False)
    wipe_area_before = models.BooleanField(default=False)
    wipe_buildnig_before = models.BooleanField(default=False)

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
        return f"PF JSON import #{self.pk} ({self.status})"

    @hook(AFTER_CREATE)
    def _enqueue(self):
        run_pfjson_import.enqueue(self.pk)


class Area(models.Model):
    """
    Административный район (address3) + агрегированные метрики объявлений
    """

    # ─────────── основные старые поля ───────────
    name = models.CharField(max_length=255, unique=True, db_index=True)
    numeric_area = models.FloatField(blank=True, null=True)

    verified_value = models.CharField(max_length=255, blank=True, null=True)
    sum_number_of_days_for_all_ads = models.PositiveIntegerField(default=0)
    numbers_of_processed_ads = models.PositiveIntegerField(default=0)
    numbers_of_main_page_ads = models.PositiveIntegerField(default=0)

    # ─────────── when take coords from pf ───────────
    geometry_json = models.JSONField(
        blank=True, null=True, help_text="Полный GeoJSON geometry мультиполигона"
    )

    CREATED_BY_CHOICES = [
        ("user", "Created manually / through admin"),
        ("geojson_import", "Imported from geojson script"),
    ]
    created_by = models.CharField(
        max_length=20, choices=CREATED_BY_CHOICES, default="user", db_index=True
    )

    # ─────────── служебное ───────────
    def __str__(self) -> str:
        return self.name or "Unnamed"

    # среднее время экспонирования объявления в районе
    @property
    def avg_days_on_market(self):
        if self.numbers_of_processed_ads:
            return round(
                self.sum_number_of_days_for_all_ads / self.numbers_of_processed_ads, 2
            )
        return None


# ─────────────────────────────── Building ─────────────────────────────────────
class Building(models.Model):
    """Жилой дом / комплекс (address1)"""

    name = models.CharField(max_length=255, db_index=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="buildings")
    dld_building = models.ForeignKey(
        DldBuilding, on_delete=models.SET_NULL, null=True, blank=True
    )
    # общая информация
    verified_value = models.CharField(max_length=255, blank=True, null=True)
    numbers_of_processed_rent_ads = models.PositiveIntegerField(default=0)
    numbers_of_processed_sale_ads = models.PositiveIntegerField(default=0)
    # ───── агрегаты по аренде (rent) ─────
    rent_count_studio = models.PositiveIntegerField(default=0)
    rent_count_1br = models.PositiveIntegerField(default=0)
    rent_count_2br = models.PositiveIntegerField(default=0)
    rent_count_3br = models.PositiveIntegerField(default=0)
    rent_count_4br = models.PositiveIntegerField(default=0)

    rent_sum_studio = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    rent_sum_1br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    rent_sum_2br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    rent_sum_3br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    rent_sum_4br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )

    # ───── агрегаты по продаже (sale) ─────
    sale_count_studio = models.PositiveIntegerField(default=0)
    sale_count_1br = models.PositiveIntegerField(default=0)
    sale_count_2br = models.PositiveIntegerField(default=0)
    sale_count_3br = models.PositiveIntegerField(default=0)
    sale_count_4br = models.PositiveIntegerField(default=0)

    sale_sum_studio = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    sale_sum_1br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    sale_sum_2br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    sale_sum_3br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )
    sale_sum_4br = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0")
    )

    # суммарная экспозиция (кол-во дней) для всех объявлений здания
    sum_exposure_rent_days = models.PositiveIntegerField(default=0)
    sum_exposure_sale_days = models.PositiveIntegerField(default=0)

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ("name", "area")

    def __str__(self):
        return f"{self.name} ({self.area.name})"

    # — средние цены —
    def _avg(self, total, count):
        return (total / count) if count else 0.0

    # аренда
    @property
    def avg_rent_studio(self):
        return self._avg(self.rent_sum_studio, self.rent_count_studio)

    @property
    def avg_rent_1br(self):
        return self._avg(self.rent_sum_1br, self.rent_count_1br)

    @property
    def avg_rent_2br(self):
        return self._avg(self.rent_sum_2br, self.rent_count_2br)

    @property
    def avg_rent_3br(self):
        return self._avg(self.rent_sum_3br, self.rent_count_3br)

    @property
    def avg_rent_4br(self):
        return self._avg(self.rent_sum_4br, self.rent_count_4br)

    # продажа
    @property
    def avg_sale_studio(self):
        return self._avg(self.sale_sum_studio, self.sale_count_studio)

    @property
    def avg_sale_1br(self):
        return self._avg(self.sale_sum_1br, self.sale_count_1br)

    @property
    def avg_sale_2br(self):
        return self._avg(self.sale_sum_2br, self.sale_count_2br)

    @property
    def avg_sale_3br(self):
        return self._avg(self.sale_sum_3br, self.sale_count_3br)

    @property
    def avg_sale_4br(self):
        return self._avg(self.sale_sum_4br, self.sale_count_4br)


from django.utils.html import format_html


# ───────────────────────────── PF‑listing абстракция ──────────────────────────
class PFBase(models.Model):
    """Общее для PF‑объявлений"""

    listing_id = models.CharField(max_length=50, unique=True, db_index=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, null=True, blank=True
    )

    url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    display_address = models.CharField(max_length=255, blank=True, null=True)
    bedrooms = models.CharField(
        max_length=10, blank=True, null=True
    )  # "studio" / "1" / …
    bathrooms = models.CharField(max_length=10, blank=True, null=True)
    added_on = models.DateTimeField(blank=True, null=True)

    broker = models.CharField(max_length=100, blank=True, null=True)
    agent = models.CharField(max_length=100, blank=True, null=True)
    agent_phone = models.CharField(max_length=50, blank=True, null=True)

    verified = models.BooleanField(default=False)
    reference = models.CharField(max_length=100, blank=True, null=True)
    broker_license_number = models.CharField(max_length=100, blank=True, null=True)

    property_type = models.CharField(max_length=50, blank=True, null=True)
    price_duration = models.CharField(
        max_length=10, blank=True, null=True
    )  # sell / rent
    listing_type = models.CharField(
        max_length=50, blank=True, null=True
    )  # Residential for …

    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    price_currency = models.CharField(max_length=10, blank=True, null=True)

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    size_min = models.CharField(max_length=50, blank=True, null=True)
    numeric_area = models.FloatField(blank=True, null=True)

    furnishing = models.CharField(max_length=10, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    description_html = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    roi = models.FloatField(
        null=True, blank=True, db_index=True, verbose_name="ROI объявления"
    )
    building_avg_roi = models.FloatField(
        null=True, blank=True, db_index=True, verbose_name="Среднее ROI по зданию"
    )

    # models.py
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["area", "verified"]),
            models.Index(fields=["building"]),
            models.Index(fields=["price"]),
            models.Index(fields=["numeric_area"]),
            models.Index(fields=["added_on"]),
            models.Index(fields=["bedrooms", "price"]),
        ]


class DisplayQuerySet(models.QuerySet):
    def __str__(self):
        # при выводе {{ qs }} в шаблоне
        return ", ".join(str(obj) for obj in self)

    # чтобы в shell и repr(qs) тоже так работало
    __repr__ = __str__


class PFListSale(PFBase):
    objects = DisplayQuerySet.as_manager()

    def __str__(self):
        return format_html(
            '<br><u><a href="{url}" target="_blank">[Sale #{title}] {building} — {listing_id}</a></u><br>',
            url=self.url,
            title=self.title or "No title",
            building=self.building,
            listing_id=self.listing_id,
        )


class PFListRent(PFBase):
    objects = DisplayQuerySet.as_manager()

    def __str__(self):
        from django.utils.html import format_html

        return format_html(
            '<BR><a href="{}" target="_blank"><i><u>[Rent #{}] {} &mdash;  </i></u></a> <BR>',
            self.url,
            self.title or "No title",
            self.building,
            self.listing_id,
        )


# ──────────────────────────────── JSON Upload ─────────────────────────────────
class PFJsonUpload(models.Model):
    upload_file = models.FileField(upload_to="pfjson")
    created_at = models.DateTimeField(auto_now_add=True)

    wipe_sale_before = models.BooleanField(default=False)
    wipe_rent_before = models.BooleanField(default=False)
    wipe_area_before = models.BooleanField(default=False)
    wipe_buildnig_before = models.BooleanField(default=False)

    def __str__(self):
        return f"PFJsonUpload {self.id}"

    # --------------------------- helpers ------------------------------------
    BEDROOM_KEYS = {
        "studio": "studio",
        "0": "studio",
        "1": "1br",
        "2": "2br",
        "3": "3br",
        "4": "4br",
    }

    def _normalize_bedroom_key(self, bedrooms_value: str) -> str:
        if not bedrooms_value:
            return "studio"  # трактуем пустое как студию
        val = str(bedrooms_value).lower().strip()
        return self.BEDROOM_KEYS.get(val, "4br")  # всё >=4 считаем как 4br

    # ---------------------------- parser ------------------------------------
    def save(self, *args, **kwargs):
        """Перехватываем save, чтобы сначала сохранить файл, а затем распарсить"""
        super().save(*args, **kwargs)

        # очистка старых данных по желанию пользователя
        if self.wipe_sale_before:
            PFListSale.objects.all().delete()
        if self.wipe_rent_before:
            PFListRent.objects.all().delete()
        if self.wipe_area_before:
            Area.objects.all().delete()
        if self.wipe_buildnig_before:
            Building.objects.all().delete()

        self.process_json()

    def process_json(self):
        """Разбор загруженного JSON‑файла и сохранение объявлений + обновление агрегатов"""
        from .models import (
            PFListSale,
            PFListRent,
        )  # локальный импорт во избежание циклов

        file_path = self.upload_file.path
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        today = timezone.now().date()
        
        # Подготавливаем списки для bulk операций
        areas_to_create = []
        areas_to_update = []
        buildings_to_create = []
        buildings_to_update = []
        listings_to_create = []
        listings_to_update = []
        
        # Кэшируем существующие объекты для избежания повторных запросов
        existing_areas = {area.name: area for area in Area.objects.all()}
        existing_buildings = {}
        for building in Building.objects.select_related('area').all():
            key = (building.name, building.area_id)
            existing_buildings[key] = building

        for item in data:
            listing_id = item.get("id")
            if not listing_id:
                continue  # без id бессмысленно

            listing_type_val = item.get(
                "type"
            )  # "Residential for Sale" / "Residential for Rent"
            if listing_type_val not in ("Residential for Sale", "Residential for Rent"):
                continue

            # фильтр по типу недвижимости (оставляем только квартиры, сравнение без учёта регистра)
            raw_property_type = (item.get("propertyType") or "").strip()
            if raw_property_type.lower() != "apartment":
                continue
            property_type_str = raw_property_type  # для записи в модель

            # --- дата объявления
            added_on_str = item.get("addedOn")
            parsed_added_on = None
            if added_on_str:
                try:
                    parsed_added_on = datetime.datetime.fromisoformat(
                        added_on_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    parsed_added_on = None

            # координаты
            coords = item.get("coordinates", {})
            lat, lng = coords.get("latitude"), coords.get("longitude")

            # площадь
            size_min_str = item.get("sizeMin") or ""
            numeric_area_val = None
            if size_min_str:
                try:
                    numeric_area_val = float(size_min_str.split()[0])
                except Exception:
                    numeric_area_val = None

            # адрес (building / area)
            disp_addr = item.get("displayAddress", "")
            parts = [x.strip() for x in disp_addr.split(",", 3)]
            while len(parts) < 4:
                parts.append("")
            address1, _, address3, _ = parts

            # ---------------- Area ----------------
            area_obj = None
            if (
                address3 and address3 in AREAS_WITH_PROPERTY
            ):  # Modified this line to check against allowed areas
                if address3 in existing_areas:
                    area_obj = existing_areas[address3]
                    # Обновляем показатели района
                    if parsed_added_on:
                        area_obj.sum_number_of_days_for_all_ads += (
                            today - parsed_added_on.date()
                        ).days
                    area_obj.numbers_of_processed_ads += 1
                    if not area_obj.verified_value:
                        area_obj.verified_value = (
                            f"{area_obj.name} ({area_obj.numbers_of_main_page_ads:,})"
                        )
                    areas_to_update.append(area_obj)
                else:
                    # Создаем новый район
                    area_obj = Area(
                        name=address3,
                        numeric_area=None,
                        numbers_of_main_page_ads=AREAS_WITH_PROPERTY.get(address3, 0),
                        sum_number_of_days_for_all_ads=0,
                        numbers_of_processed_ads=1,
                        verified_value=f"{address3} ({AREAS_WITH_PROPERTY.get(address3, 0):,})"
                    )
                    if parsed_added_on:
                        area_obj.sum_number_of_days_for_all_ads += (
                            today - parsed_added_on.date()
                        ).days
                    areas_to_create.append(area_obj)
                    existing_areas[address3] = area_obj

            # ---------------- Building ----------------
            building_obj = None
            if address1 and area_obj:
                building_key = (address1, area_obj.id)
                if building_key in existing_buildings:
                    building_obj = existing_buildings[building_key]
                    # Обновляем существующее здание
                    if lat is not None and lng is not None:
                        building_obj.latitude = lat
                        building_obj.longitude = lng
                    
                    # Инкрементируем общее кол-во объявлений
                    if listing_type_val == "Residential for Rent":
                        building_obj.numbers_of_processed_rent_ads += 1
                    else:
                        building_obj.numbers_of_processed_sale_ads += 1
                    
                    # Категория по спальням
                    bedroom_key = self._normalize_bedroom_key(item.get("bedrooms"))
                    price_val = item.get("price") or 0
                    price_val = Decimal(str(price_val))
                    
                    # Сколько дней на рынке
                    days_on_market = 0
                    if parsed_added_on:
                        days_on_market = (today - parsed_added_on.date()).days
                    
                    # Обновляем счетчики
                    if listing_type_val == "Residential for Rent":
                        setattr(
                            building_obj,
                            f"rent_count_{bedroom_key}",
                            getattr(building_obj, f"rent_count_{bedroom_key}") + 1,
                        )
                        setattr(
                            building_obj,
                            f"rent_sum_{bedroom_key}",
                            getattr(building_obj, f"rent_sum_{bedroom_key}") + price_val,
                        )
                        building_obj.sum_exposure_rent_days += days_on_market
                    elif listing_type_val == "Residential for Sale":
                        setattr(
                            building_obj,
                            f"sale_count_{bedroom_key}",
                            getattr(building_obj, f"sale_count_{bedroom_key}") + 1,
                        )
                        setattr(
                            building_obj,
                            f"sale_sum_{bedroom_key}",
                            getattr(building_obj, f"sale_sum_{bedroom_key}") + price_val,
                        )
                        building_obj.sum_exposure_sale_days += days_on_market
                    
                    buildings_to_update.append(building_obj)
                else:
                    # Создаем новое здание
                    building_obj = Building(
                        name=address1,
                        area=area_obj,
                        latitude=lat,
                        longitude=lng,
                        numbers_of_processed_rent_ads=1 if listing_type_val == "Residential for Rent" else 0,
                        numbers_of_processed_sale_ads=1 if listing_type_val == "Residential for Sale" else 0
                    )
                    
                    # Инициализируем счетчики
                    bedroom_key = self._normalize_bedroom_key(item.get("bedrooms"))
                    price_val = item.get("price") or 0
                    price_val = Decimal(str(price_val))
                    days_on_market = 0
                    if parsed_added_on:
                        days_on_market = (today - parsed_added_on.date()).days
                    
                    if listing_type_val == "Residential for Rent":
                        setattr(building_obj, f"rent_count_{bedroom_key}", 1)
                        setattr(building_obj, f"rent_sum_{bedroom_key}", price_val)
                        building_obj.sum_exposure_rent_days = days_on_market
                    elif listing_type_val == "Residential for Sale":
                        setattr(building_obj, f"sale_count_{bedroom_key}", 1)
                        setattr(building_obj, f"sale_sum_{bedroom_key}", price_val)
                        building_obj.sum_exposure_sale_days = days_on_market
                    
                    buildings_to_create.append(building_obj)
                    existing_buildings[building_key] = building_obj

            # ------------------------------------------------------------------
            # Теперь САМЫЕ ГЛАВНЫЕ изменения — сохраняем само объявление
            # ------------------------------------------------------------------
            model_class = (
                PFListRent if listing_type_val == "Residential for Rent" else PFListSale
            )
            price_duration_val = (
                "rent" if listing_type_val == "Residential for Rent" else "sell"
            )

            # Подготавливаем данные для объявления
            listing_data = {
                "area": area_obj,
                "building": building_obj,
                # ---- базовые поля --------------------------------------------------
                "url": _clean_str(item.get("url")),
                "title": _clean_str(item.get("title")),
                "display_address": _clean_str(disp_addr),
                "bedrooms": _clean_str(item.get("bedrooms")),
                "bathrooms": _clean_str(item.get("bathrooms")),
                "added_on": parsed_added_on,
                # ---- агент / брокер ------------------------------------------------
                "broker": _clean_str(item.get("brokerName")),
                "agent": _clean_str(item.get("agentName")),
                "agent_phone": _clean_str(item.get("phone")),
                "verified": bool(item.get("verified")),
                "reference": _clean_str(item.get("reference")),
                "broker_license_number": _clean_str(item.get("brokerLicenseNo")),
                # ---- типы / цены ---------------------------------------------------
                "property_type": _clean_str(property_type_str),
                "price_duration": price_duration_val,
                "listing_type": listing_type_val,
                "price": Decimal(str(item.get("price") or 0)),
                "price_currency": _clean_str(item.get("priceCurrency")),
                # ---- координаты / площадь -----------------------------------------
                "latitude": lat,
                "longitude": lng,
                "size_min": size_min_str or None,
                "numeric_area": numeric_area_val,
                # ---- прочее --------------------------------------------------------
                "furnishing": _clean_str(item.get("furnishing")),
                "description": _clean_str(item.get("description")),
                "description_html": _clean_str(item.get("descriptionHtml")),
            }
            
            # Проверяем, существует ли уже объявление
            try:
                existing_listing = model_class.objects.get(listing_id=listing_id)
                # Обновляем существующее объявление
                for field, value in listing_data.items():
                    if value is not None:
                        setattr(existing_listing, field, value)
                listings_to_update.append(existing_listing)
            except model_class.DoesNotExist:
                # Создаем новое объявление
                new_listing = model_class(listing_id=listing_id, **listing_data)
                listings_to_create.append(new_listing)

        # Выполняем bulk операции
        if areas_to_create:
            Area.objects.bulk_create(areas_to_create)
        
        if areas_to_update:
            Area.objects.bulk_update(
                areas_to_update,
                fields=[
                    'sum_number_of_days_for_all_ads',
                    'numbers_of_processed_ads',
                    'verified_value'
                ]
            )
        
        if buildings_to_create:
            Building.objects.bulk_create(buildings_to_create)
        
        if buildings_to_update:
            Building.objects.bulk_update(
                buildings_to_update,
                fields=[
                    'latitude', 'longitude', 'numbers_of_processed_rent_ads',
                    'numbers_of_processed_sale_ads', 'sum_exposure_rent_days',
                    'sum_exposure_sale_days'
                ] + [f'rent_count_{key}' for key in self.BEDROOM_KEYS.values()] +
                     [f'rent_sum_{key}' for key in self.BEDROOM_KEYS.values()] +
                     [f'sale_count_{key}' for key in self.BEDROOM_KEYS.values()] +
                     [f'sale_sum_{key}' for key in self.BEDROOM_KEYS.values()]
            )
        
        if listings_to_create:
            model_class.objects.bulk_create(listings_to_create)
        
        if listings_to_update:
            model_class.objects.bulk_update(
                listings_to_update,
                fields=[
                    'area', 'building', 'url', 'title', 'display_address',
                    'bedrooms', 'bathrooms', 'added_on', 'broker', 'agent',
                    'agent_phone', 'verified', 'reference', 'broker_license_number',
                    'property_type', 'price_duration', 'listing_type', 'price',
                    'price_currency', 'latitude', 'longitude', 'size_min',
                    'numeric_area', 'furnishing', 'description', 'description_html'
                ]
            )

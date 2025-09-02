# realty/reports/models.py

import json
import statistics
from datetime import timedelta, date

from typing import Optional

from django.db import models, transaction

from django.db.models import JSONField
from django.utils import timezone
from django.core.exceptions import ValidationError

from realty.pfimport.models import Building, PFListSale, PFListRent, Area
from .utils import (
    _bedrooms_to_int,
    get_room_int_and_units,
    get_room_int_and_units_2,
    ROOM_MAPPING,
)
from realty.main.models import (
    Building as DldBuilding,
    MergedTransaction,
    MergedRentalTransaction,
)
from realty.main.models import Area as DldArea
import re


from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


BEDROOM_CHOICES = [
    ("studio", "Studio"),
    ("1br", "1 B/R"),
    ("2br", "2 B/R"),
    ("3br", "3 B/R"),
    ("4br", "4 B/R"),
]


class BuildingReport(models.Model):
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="reports"
    )
    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES)
    calculated_at = models.DateTimeField(auto_now=True)

    # ── SALE metrics ───────────────────────────────────────────────────────────
    avg_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    sale_count = models.PositiveIntegerField(default=0)
    avg_exposure_sale_days = models.FloatField(null=True, blank=True)
    sale_per_unit_ratio = models.FloatField(null=True, blank=True)

    # ── RENT metrics ───────────────────────────────────────────────────────────
    avg_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    rent_count = models.PositiveIntegerField(default=0)
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)
    rent_per_unit_ratio = models.FloatField(null=True, blank=True)

    # ── JSON from DLD ──────────────────────────────────────────────────────────
    type_of_rooms_in = JSONField(blank=True, null=True)

    # ── ROI ─────────────────────────────────────────────────────────────────────
    roi = models.FloatField(null=True, blank=True)

    # --connections
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)

    dld_building = models.ForeignKey(
        DldBuilding, on_delete=models.SET_NULL, null=True, blank=True
    )
    dld_area = models.ForeignKey(
        DldArea, on_delete=models.SET_NULL, null=True, blank=True
    )

    total_units = models.PositiveIntegerField(default=0)

    units = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("building", "bedrooms")

    def clean(self):
        """Проверка при ручном создании записи через админ-форму."""
        if not self.building or not self.building.dld_building:
            raise ValidationError(
                "Отчёт можно строить только для зданий с привязанным DLD-объектом."
            )

    #  ──────────────────────────────────────────────────────────────────

    # ──────────────────────────  Публичный интерфейс  ──────────────────────────
    @classmethod
    def calculate(
        cls,
        building: "Building",
        bedrooms: str,
    ) -> "BuildingReport | None":
        """
        Пересчитывает все метрики для (building, bedrooms).

        ▸ Возвращает `BuildingReport` или `None`, если расчёт невозможен
        ▸ Метод **никогда** не выбрасывает исключения (полезно для вызовов из админки)
        """

        # ── 0. Базовые проверки ───────────────────────────────────────────────
        if not (building and building.dld_building):
            return None

        bed_int, units = get_room_int_and_units_2(building, bedrooms)
        if not (bed_int and units):
            return None

        # ── 1. Константы ──────────────────────────────────────────────────────
        now = timezone.now()
        one_year_ago = now - timedelta(days=365)
        dld_building = building.dld_building
        total_units = dld_building.total_units or 0
        area = building.area

        # ── 2. rooms_count из arabic_name (json) ──────────────────────────────
        try:
            rooms_count_json: dict[str, int] = json.loads(
                dld_building.arabic_name or "{}"
            ).get("rooms_count", {})
        except (TypeError, ValueError):
            rooms_count_json = {}

        # ── 3. Утилита для «безопасной» статистики ────────────────────────────
        def safe(fn: Callable[[Iterable[T]], T], seq: list[T]) -> T | None:  # noqa: ANN401
            return fn(seq) if seq else None

        # ── 4. SALE ───────────────────────────────────────────────────────────
        sale_prices = [
            float(p)
            for p in PFListSale.objects.filter(
                building=building,
                bedrooms__iexact=bed_int,
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        sale_count = len(sale_prices)
        avg_sale = safe(statistics.fmean, sale_prices)
        median_sale = safe(statistics.median, sale_prices)
        min_sale = safe(min, sale_prices)
        max_sale = safe(max, sale_prices)
        avg_expo_sale = (
            building.sum_exposure_sale_days / building.numbers_of_processed_sale_ads
            if building.numbers_of_processed_sale_ads
            else None
        )
        sale_per_unit = sale_count / units if units else None  # ★ исправлено

        # ── 5. RENT ───────────────────────────────────────────────────────────
        rent_prices = [
            float(p)
            for p in PFListRent.objects.filter(
                building=building,
                bedrooms__iexact=bed_int,
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        rent_count = len(rent_prices)
        avg_rent = safe(statistics.fmean, rent_prices)
        median_rent = safe(statistics.median, rent_prices)
        min_rent = safe(min, rent_prices)
        max_rent = safe(max, rent_prices)
        avg_expo_rent = (
            building.sum_exposure_rent_days / building.numbers_of_processed_rent_ads
            if building.numbers_of_processed_rent_ads
            else None
        )
        rent_per_unit = rent_count / units if units else None  # ★ исправлено

        # ── 6. ROI  (простой, без годового множителя) ────────────────────────
        roi = (avg_rent / avg_sale) if (avg_rent and avg_sale) else None

        # ── 7. Запись в БД ────────────────────────────────────────────────────
        with transaction.atomic():
            report, _ = cls.objects.update_or_create(
                building=building,
                bedrooms=bedrooms,
                defaults={
                    # ---- sale ----
                    "avg_sale_price": avg_sale,
                    "median_sale_price": median_sale,
                    "min_sale_price": min_sale,
                    "max_sale_price": max_sale,
                    "sale_count": sale_count,
                    "avg_exposure_sale_days": avg_expo_sale,
                    "sale_per_unit_ratio": sale_per_unit,
                    # ---- rent ----
                    "avg_rent_price": avg_rent,
                    "median_rent_price": median_rent,
                    "min_rent_price": min_rent,
                    "max_rent_price": max_rent,
                    "rent_count": rent_count,
                    "avg_exposure_rent_days": avg_expo_rent,
                    "rent_per_unit_ratio": rent_per_unit,
                    # ---- misc ----
                    "type_of_rooms_in": rooms_count_json,
                    "total_units": total_units,
                    "roi": roi,
                    "area": area,
                    "dld_building": dld_building,
                    "units": units,
                },
            )
        return report

    def __str__(self):
        return f"Отчёт по {self.building} / {self.get_bedrooms_display()}"


class AreaReport(models.Model):
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, related_name="area_reports"
    )
    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES)
    calculated_at = models.DateTimeField(auto_now=True)

    # агрегаты по всем объявлениям в районе
    avg_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # агрегаты «средних по зданию»
    avg_sale_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # разброс цен
    median_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # ── НОВЫЕ ПОЛЯ: средняя экспозиция по району ─────────────────────────────────  ← NEW
    avg_exposure_sale_days = models.FloatField(null=True, blank=True)  # ← NEW
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)  # ← NEW

    # ── НОВОЕ ПОЛЕ: среднее sale_per_unit_ratio по району ───────────────────────  ← NEW
    avg_sale_per_unit_ratio = models.FloatField(null=True, blank=True)  # ← NEW

    # усреднённые показатели из BuildingReport
    avg_rent_per_unit_ratio = models.FloatField(null=True, blank=True)
    avg_roi = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("area", "bedrooms")

    @classmethod
    def calculate(cls, area: Area, bedrooms: str) -> Optional["AreaReport"]:
        """
        Считает все метрики для данной Area и комнатности и создаёт/обновляет запись.
        """
        one_year_ago = timezone.now() - timedelta(days=365)

        # 1) определяем DLD-ключ для sale и normalize bedrooms
        print(bedrooms)
        dld_key = ROOM_MAPPING.get(bedrooms, [bedrooms])[0]
        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None

        # 2) все объявления sale в этом районе
        sale_qs = PFListSale.objects.filter(
            building__area=area, bedrooms__iexact=bed_int, added_on__gte=one_year_ago
        ).values_list("price", flat=True)
        sale_prices = [p for p in sale_qs if p is not None]

        # 3) все объявления rent в этом районе
        rent_qs = PFListRent.objects.filter(
            building__area=area, bedrooms__iexact=bed_int, added_on__gte=one_year_ago
        ).values_list("price", flat=True)
        rent_prices = [p for p in rent_qs if p is not None]

        # 4) средние по всем объявлениям
        avg_sale_all = sum(sale_prices) / len(sale_prices) if sale_prices else None
        avg_rent_all = sum(rent_prices) / len(rent_prices) if rent_prices else None

        # -------------------------------------------------------------------------
        # единый QuerySet с объектами BuildingReport для данного area + bedrooms
        # -------------------------------------------------------------------------
        br_qs = BuildingReport.objects.filter(
            building__area=area,
            bedrooms=bedrooms,
        )

        # -- средние цены по зданиям ----------------------------------------------
        sale_build_avgs = [
            r.avg_sale_price for r in br_qs if r.avg_sale_price is not None
        ]
        rent_build_avgs = [
            r.avg_rent_price for r in br_qs if r.avg_rent_price is not None
        ]

        avg_sale_by_build = (
            sum(sale_build_avgs) / len(sale_build_avgs) if sale_build_avgs else None
        )
        avg_rent_by_build = (
            sum(rent_build_avgs) / len(rent_build_avgs) if rent_build_avgs else None
        )

        # 6) медианы / мин / макс
        med_sale = statistics.median(sale_prices) if sale_prices else None
        med_rent = statistics.median(rent_prices) if rent_prices else None
        min_sale = min(sale_prices) if sale_prices else None
        max_sale = max(sale_prices) if sale_prices else None
        min_rent = min(rent_prices) if rent_prices else None
        max_rent = max(rent_prices) if rent_prices else None

        # -- коэффициенты ----------------------------------------------------------
        ratios = [
            r.rent_per_unit_ratio for r in br_qs if r.rent_per_unit_ratio is not None
        ]
        rois = [r.roi for r in br_qs if r.roi is not None]

        avg_ratio = sum(ratios) / len(ratios) if ratios else None
        avg_roi = sum(rois) / len(rois) if rois else None

        # -- НОВОЕ: экспозиция и sale_per_unit_ratio -------------------------------
        expo_sale_vals = [
            r.avg_exposure_sale_days
            for r in br_qs
            if r.avg_exposure_sale_days is not None
        ]
        expo_rent_vals = [
            r.avg_exposure_rent_days
            for r in br_qs
            if r.avg_exposure_rent_days is not None
        ]
        # print(r, br_qs)
        avg_expo_sale = (
            sum(expo_sale_vals) / len(expo_sale_vals) if expo_sale_vals else None
        )
        avg_expo_rent = (
            sum(expo_rent_vals) / len(expo_rent_vals) if expo_rent_vals else None
        )

        sale_ratio_vals = [
            r.sale_per_unit_ratio for r in br_qs if r.sale_per_unit_ratio is not None
        ]
        avg_sale_ratio = (
            sum(sale_ratio_vals) / len(sale_ratio_vals) if sale_ratio_vals else None
        )

        # 8) создаём или обновляем отчёт
        report, _ = cls.objects.update_or_create(
            area=area,
            bedrooms=bedrooms,
            defaults={
                "avg_sale_price": avg_sale_all,
                "avg_rent_price": avg_rent_all,
                "avg_sale_price_by_building": avg_sale_by_build,
                "avg_rent_price_by_building": avg_rent_by_build,
                "median_sale_price": med_sale,
                "median_rent_price": med_rent,
                "min_sale_price": min_sale,
                "max_sale_price": max_sale,
                "min_rent_price": min_rent,
                "max_rent_price": max_rent,
                "avg_rent_per_unit_ratio": avg_ratio,
                "avg_roi": avg_roi,
                # ── новые поля ───────────────────────────────────────────────
                "avg_exposure_sale_days": avg_expo_sale,
                "avg_exposure_rent_days": avg_expo_rent,
                "avg_sale_per_unit_ratio": avg_sale_ratio,
            },
        )
        return report


import statistics  # === NEW ===
from datetime import timedelta, date  # === NEW ===
from decimal import Decimal  # === NEW ===

from django.db import models, transaction
from django.utils import timezone

# здесь BEDROOM_CHOICES, _bedrooms_to_int, ROOM_MAPPING
# и модели PFListSale/Rent, BuildingReport должны быть уже импортированы
# ---------------------------------------------------------------------


class CityReportPF(models.Model):
    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES, unique=True)
    calculated_at = models.DateTimeField(auto_now=True)

    # ── SALE ───────────────────────────────────────────────────────────
    avg_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_exposure_days = models.FloatField(null=True, blank=True)

    # ── RENT ───────────────────────────────────────────────────────────
    avg_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)

    # ── RATIOS ─────────────────────────────────────────────────────────
    avg_rent_per_unit_ratio = models.FloatField(null=True, blank=True)
    avg_roi = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio = models.FloatField(null=True, blank=True)

    # ── LY / PY  (15-05) ───────────────────────────────────────────────
    avg_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_ly = models.PositiveIntegerField(null=True, blank=True)
    count_sale_py = models.PositiveIntegerField(null=True, blank=True)

    avg_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_rent_ly = models.PositiveIntegerField(null=True, blank=True)
    count_rent_py = models.PositiveIntegerField(null=True, blank=True)

    # per-unit ratios
    avg_rent_per_unit_ratio_ly = models.FloatField(null=True, blank=True)
    avg_rent_per_unit_ratio_py = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio_ly = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio_py = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Отчёт по городу"
        verbose_name_plural = "Отчёты по городу"

    # ------------------------------------------------------------------
    #                      ГЛАВНЫЙ ПЕРЕСЧЁТ
    # ------------------------------------------------------------------
    @classmethod
    def calculate(cls, bedrooms: str) -> "CityReport | None":
        """
        Пересчитать ВСЕ метрики для одной комнатности по городу.
        """
        from .models import PFListSale, PFListRent, BuildingReport  # локальные импорты

        today = timezone.now().date()
        start_ly = today - timedelta(days=365)
        start_py = today - timedelta(days=730)
        end_py = start_ly - timedelta(days=1)

        # --- bedrooms normalisation -----------------------------------
        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None

        # helper: статистика над списком чисел --------------------------
        def stat(nums):
            if not nums:
                return (None, None, None, None, 0)
            return (
                sum(nums) / len(nums),
                statistics.median(nums),
                min(nums),
                max(nums),
                len(nums),
            )

        # =========================  SALE  ==============================
        sale_prices_ly = list(
            PFListSale.objects.filter(
                bedrooms__iexact=bed_int, added_on__range=(start_ly, today)
            ).values_list("price", flat=True)
        )
        sale_prices_ly = [float(p) for p in sale_prices_ly if p]
        (avg_price, median_price, min_price, max_price, cnt_sale_ly) = stat(
            sale_prices_ly
        )

        sale_prices_py = list(
            PFListSale.objects.filter(
                bedrooms__iexact=bed_int, added_on__range=(start_py, end_py)
            ).values_list("price", flat=True)
        )
        sale_prices_py = [float(p) for p in sale_prices_py if p]
        (avg_price_py, median_price_py, min_price_py, max_price_py, cnt_sale_py) = stat(
            sale_prices_py
        )

        # =========================  RENT  ==============================
        rent_prices_ly = list(
            PFListRent.objects.filter(
                bedrooms__iexact=bed_int, added_on__range=(start_ly, today)
            ).values_list("price", flat=True)
        )
        rent_prices_ly = [float(p) for p in rent_prices_ly if p]
        (
            avg_rent_price,
            median_rent_price,
            min_rent_price,
            max_rent_price,
            cnt_rent_ly,
        ) = stat(rent_prices_ly)

        rent_prices_py = list(
            PFListRent.objects.filter(
                bedrooms__iexact=bed_int, added_on__range=(start_py, end_py)
            ).values_list("price", flat=True)
        )
        rent_prices_py = [float(p) for p in rent_prices_py if p]
        (
            avg_rent_price_py,
            median_rent_price_py,
            min_rent_price_py,
            max_rent_price_py,
            cnt_rent_py,
        ) = stat(rent_prices_py)

        # если за LY нет совсем ни продаж ни аренды – отчёт не создаём
        if cnt_sale_ly == 0 and cnt_rent_ly == 0:
            return None

        # =================  METRICS FROM BuildingReport  ================
        br_qs = BuildingReport.objects.filter(bedrooms=bedrooms)

        # цены «по зданиям»
        sale_build_avgs = [float(b.avg_sale_price) for b in br_qs if b.avg_sale_price]
        avg_price_by_building = (
            (sum(sale_build_avgs) / len(sale_build_avgs)) if sale_build_avgs else None
        )

        rent_build_avgs = [float(b.avg_rent_price) for b in br_qs if b.avg_rent_price]
        avg_rent_price_by_building = (
            (sum(rent_build_avgs) / len(rent_build_avgs)) if rent_build_avgs else None
        )

        # экспозиция
        expos_sale = [
            b.avg_exposure_sale_days for b in br_qs if b.avg_exposure_sale_days
        ]
        avg_exposure = (sum(expos_sale) / len(expos_sale)) if expos_sale else None

        expos_rent = [
            b.avg_exposure_rent_days for b in br_qs if b.avg_exposure_rent_days
        ]
        avg_exposure_rent = (sum(expos_rent) / len(expos_rent)) if expos_rent else None

        # ratios
        rent_ratios = [
            b.rent_per_unit_ratio for b in br_qs if b.rent_per_unit_ratio is not None
        ]  # === NEW ===
        avg_rent_ratio = (sum(rent_ratios) / len(rent_ratios)) if rent_ratios else None

        sale_ratios = [
            b.sale_per_unit_ratio for b in br_qs if b.sale_per_unit_ratio is not None
        ]  # === NEW ===
        avg_sale_ratio = (sum(sale_ratios) / len(sale_ratios)) if sale_ratios else None

        # ROI
        rois = 0.0  # [b.roi_ly for b in br_qs if b.roi_ly is not None]  # подразумеваем roi_ly в BuildingReport
        avg_roi = 0.0  # (sum(rois) / len(rois)) if rois else None

        # -------- LY / PY ratios --------------------------------------
        rent_ratios_ly = [
            b.rent_per_unit_ratio for b in br_qs if b.rent_per_unit_ratio is not None
        ]
        rent_ratios_py = [
            b.rent_per_unit_ratio for b in br_qs if b.rent_per_unit_ratio is not None
        ]
        sale_ratios_ly = [
            b.sale_per_unit_ratio for b in br_qs if b.sale_per_unit_ratio is not None
        ]
        sale_ratios_py = [
            b.sale_per_unit_ratio for b in br_qs if b.sale_per_unit_ratio is not None
        ]

        avg_rent_ratio_ly = (
            (sum(rent_ratios_ly) / len(rent_ratios_ly)) if rent_ratios_ly else None
        )  # === NEW ===
        avg_rent_ratio_py = (
            (sum(rent_ratios_py) / len(rent_ratios_py)) if rent_ratios_py else None
        )  # === NEW ===
        avg_sale_ratio_ly = (
            (sum(sale_ratios_ly) / len(sale_ratios_ly)) if sale_ratios_ly else None
        )  # === NEW ===
        avg_sale_ratio_py = (
            (sum(sale_ratios_py) / len(sale_ratios_py)) if sale_ratios_py else None
        )  # === NEW ===

        # =======================  SAVE  ================================
        with transaction.atomic():
            report, _ = cls.objects.update_or_create(
                bedrooms=bedrooms,
                defaults={
                    # --- SALE current ---
                    "avg_price": avg_price,
                    "median_price": median_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price_by_building": avg_price_by_building,
                    "avg_exposure_days": avg_exposure,
                    # --- RENT current ---
                    "avg_rent_price": avg_rent_price,
                    "median_rent_price": median_rent_price,
                    "min_rent_price": min_rent_price,
                    "max_rent_price": max_rent_price,
                    "avg_rent_price_by_building": avg_rent_price_by_building,
                    "avg_exposure_rent_days": avg_exposure_rent,
                    # --- RATIOS current ---
                    "avg_rent_per_unit_ratio": avg_rent_ratio,
                    "avg_sale_per_unit_ratio": avg_sale_ratio,
                    "avg_roi": avg_roi,
                    # --- SALE LY / PY ---
                    "avg_price_ly": avg_price,
                    "avg_price_py": avg_price_py,
                    "median_price_ly": median_price,
                    "median_price_py": median_price_py,
                    "min_price_ly": min_price,
                    "min_price_py": min_price_py,
                    "max_price_ly": max_price,
                    "max_price_py": max_price_py,
                    "count_sale_ly": cnt_sale_ly,
                    "count_sale_py": cnt_sale_py,
                    # --- RENT LY / PY ---
                    "avg_rent_price_ly": avg_rent_price,
                    "avg_rent_price_py": avg_rent_price_py,
                    "median_rent_price_ly": median_rent_price,
                    "median_rent_price_py": median_rent_price_py,
                    "min_rent_price_ly": min_rent_price,
                    "min_rent_price_py": min_rent_price_py,
                    "max_rent_price_ly": max_rent_price,
                    "max_rent_price_py": max_rent_price_py,
                    "count_rent_ly": cnt_rent_ly,
                    "count_rent_py": cnt_rent_py,
                    # --- RATIOS LY / PY ---
                    "avg_rent_per_unit_ratio_ly": avg_rent_ratio_ly,  # === NEW ===
                    "avg_rent_per_unit_ratio_py": avg_rent_ratio_py,  # === NEW ===
                    "avg_sale_per_unit_ratio_ly": avg_sale_ratio_ly,  # === NEW ===
                    "avg_sale_per_unit_ratio_py": avg_sale_ratio_py,  # === NEW ===
                },
            )
        return report

    # ------------------------------------------------------------------
    def __str__(self):
        return f"Городской отчёт pf / {self.get_bedrooms_display()}"


class CityReport(models.Model):
    avg_ppsqm_rent_by_building = models.DecimalField(
        max_digits=15,
        decimal_places=2,  # ★ NEW (LY)
        null=True,
        blank=True,
    )
    avg_sqm_by_building = models.FloatField(null=True, blank=True)  # ★ NEW (LY)
    avg_ppsqm_by_building = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )  # ★ NEW (LY)
    avg_sqm_by_building_py = models.FloatField(null=True, blank=True)  # ★ NEW (PY)
    avg_ppsqm_by_building_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_ppsqm_rent_by_building_py = models.DecimalField(
        max_digits=15,
        decimal_places=2,  # ★ NEW (PY)
        null=True,
        blank=True,
    )
    avg_roi_py = models.FloatField(null=True, blank=True)  # ★ NEW (PY)

    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES, unique=True)
    calculated_at = models.DateTimeField(auto_now=True)

    # ── SALE ───────────────────────────────────────────────────────────
    avg_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_exposure_days = models.FloatField(null=True, blank=True)

    # ── RENT ───────────────────────────────────────────────────────────
    avg_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_by_building = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    median_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_rent_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)

    # ── RATIOS ─────────────────────────────────────────────────────────
    avg_rent_per_unit_ratio = models.FloatField(null=True, blank=True)
    avg_roi = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio = models.FloatField(null=True, blank=True)

    # ── LY / PY  (15-05) ───────────────────────────────────────────────
    avg_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_ly = models.PositiveIntegerField(null=True, blank=True)
    count_sale_py = models.PositiveIntegerField(null=True, blank=True)

    avg_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_ly = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_rent_ly = models.PositiveIntegerField(null=True, blank=True)
    count_rent_py = models.PositiveIntegerField(null=True, blank=True)

    # per-unit ratios
    avg_rent_per_unit_ratio_ly = models.FloatField(null=True, blank=True)
    avg_rent_per_unit_ratio_py = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio_ly = models.FloatField(null=True, blank=True)
    avg_sale_per_unit_ratio_py = models.FloatField(null=True, blank=True)
    # ★ NEW: площадь и цена за кв.м (среднее по билдингу в Дубае)
    avg_sqm_by_building = models.FloatField(null=True, blank=True)  # ★ NEW
    avg_ppsqm_by_building = models.DecimalField(
        max_digits=15,
        decimal_places=2,  # ★ NEW
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Отчёт по городуDLD"
        verbose_name_plural = "Отчёты по городуDLD"

    @classmethod
    def calculate(cls, bedrooms: str) -> "CityReport | None":
        """
        Полный пересчёт всех метрик по Дубаю для одной комнатности.

        • «Текущий год» (LY) – по *сырым* объявлениям PFListSale / PFListRent
        • «Прошлый год» (PY)   – по агрегатам DldBuildingReport
        • Все «по-зданиям» метрики (avg_*_by_building, avg_*_per_unit_ratio, ROI,
          экспозиция) берутся из **DldBuildingReport**, усредняя по всем зданиям.
        """

        # ──────────────────────────────────────────────────────────────
        #           ИМПОРТЫ + ДАТЫ
        # ──────────────────────────────────────────────────────────────
        from datetime import timedelta
        from django.utils import timezone
        import statistics
        from .models import PFListSale, PFListRent, DldBuildingReport  # ★ NEW

        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)

        # ──────────────────────────────────────────────────────────────
        #           NORMALISE BEDROOMS
        # ──────────────────────────────────────────────────────────────
        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None

        # ──────────────────────────────────────────────────────────────
        #           HELPERS
        # ──────────────────────────────────────────────────────────────
        def _stat(values):
            """avg, median, min, max, count  for a list of floats"""
            if not values:
                return None, None, None, None, 0
            return (
                sum(values) / len(values),
                statistics.median(values),
                min(values),
                max(values),
                len(values),
            )

        def _fmean_attr(qs, attr):  # ★ NEW
            vals = [
                float(getattr(r, attr, None))
                for r in qs
                if getattr(r, attr, None) is not None
            ]
            return sum(vals) / len(vals) if vals else None

        def _fmedian_attr(qs, attr):  # ★ NEW
            vals = [
                float(getattr(r, attr, None))
                for r in qs
                if getattr(r, attr, None) is not None
            ]
            return statistics.median(vals) if vals else None

        # ──────────────────────────────────────────────────────────────
        #           RAW ADS  (LY)
        # ──────────────────────────────────────────────────────────────
        sale_vals_ly = list(
            PFListSale.objects.filter(
                bedrooms__iexact=bed_int, added_on__gte=one_year_ago
            ).values_list("price", flat=True)
        )
        sale_vals_ly = [float(p) for p in sale_vals_ly if p]

        rent_vals_ly = list(
            PFListRent.objects.filter(
                bedrooms__iexact=bed_int, added_on__gte=one_year_ago
            ).values_list("price", flat=True)
        )
        rent_vals_ly = [float(p) for p in rent_vals_ly if p]

        # если совсем нет сделок – отчёт не создаём
        if not sale_vals_ly and not rent_vals_ly:
            return None

        (avg_price, median_price, min_price, max_price, cnt_sale_ly) = _stat(
            sale_vals_ly
        )

        (
            avg_rent_price,
            median_rent_price,
            min_rent_price,
            max_rent_price,
            cnt_rent_ly,
        ) = _stat(rent_vals_ly)

        # ──────────────────────────────────────────────────────────────
        #           BUILDING-LEVEL АГРЕГАТЫ  (LY / PY)
        # ──────────────────────────────────────────────────────────────
        br_qs = DldBuildingReport.objects.filter(bedrooms=bedrooms)  # ★ NEW

        # # --- LY -------------------------------------------------------
        # avg_price_by_building          = _fmean_attr(br_qs, "avg_sale_price_ly")   # ★ NEW
        # avg_rent_price_by_building     = _fmean_attr(br_qs, "avg_rent_price_ly")   # ★ NEW
        avg_exposure_days = _fmean_attr(br_qs, "avg_exposure_sale_days")  # ★ NEW
        # avg_exposure_rent_days         = _fmean_attr(br_qs, "avg_exposure_rent_days")  # ★ NEW
        # avg_sale_per_unit_ratio        = _fmean_attr(br_qs, "avg_sale_per_unit_ratio") # ★ NEW

        # ====== LY (усредняем по билдингу) ============================
        avg_price_by_building = _fmean_attr(br_qs, "avg_sale_price_ly")
        avg_rent_price_by_building = _fmean_attr(br_qs, "avg_rent_price_ly")
        # avg_exposure_days          = _fmean_attr(br_qs, "avg_exposure_sale_days")
        avg_exposure_rent_days = _fmean_attr(br_qs, "avg_exposure_rent_days")
        avg_sale_per_unit_ratio = _fmean_attr(br_qs, "avg_sale_per_unit_ratio")

        # ★ NEW:
        avg_sqm_by_building = _fmean_attr(br_qs, "avg_sqm_sale_ly")  # ★ NEW
        avg_ppsqm_by_building = _fmean_attr(br_qs, "avg_ppsqm_sale_ly")  # ★ NEW
        # rent-per-unit ratio: берём годовую частоту сделок аренды на юнит
        rent_ratio_vals = [
            (r.tx_per_unit_pm_ly_rent or 0) * 12
            for r in br_qs
            if r.tx_per_unit_pm_ly_rent is not None
        ]  # ★ NEW
        avg_rent_per_unit_ratio = (
            (sum(rent_ratio_vals) / len(rent_ratio_vals)) if rent_ratio_vals else None
        )  # ★ NEW

        avg_roi = _fmean_attr(br_qs, "roi_ly")  # ★ NEW

        # --- PY -------------------------------------------------------
        avg_price_py = _fmean_attr(br_qs, "avg_sale_price_py")  # ★ NEW
        median_price_py = _fmedian_attr(br_qs, "avg_sale_price_py")  # ★ NEW
        min_price_py = _fmean_attr(br_qs, "min_sale_price_py")  # ★ NEW
        max_price_py = _fmean_attr(br_qs, "max_sale_price_py")  # ★ NEW
        count_sale_py = _fmean_attr(br_qs, "count_sale_py")  # ★ NEW

        avg_rent_price_py = _fmean_attr(br_qs, "avg_rent_price_py")  # ★ NEW
        median_rent_price_py = _fmedian_attr(br_qs, "avg_rent_price_py")  # ★ NEW
        min_rent_price_py = _fmean_attr(br_qs, "min_rent_price_py")  # ★ NEW
        max_rent_price_py = _fmean_attr(br_qs, "max_rent_price_py")  # ★ NEW
        count_rent_py = _fmean_attr(br_qs, "count_rent_py")  # ★ NEW

        avg_price_by_building_py = _fmean_attr(br_qs, "avg_sale_price_py")  # ★ NEW
        avg_rent_price_by_building_py = _fmean_attr(br_qs, "avg_rent_price_py")  # ★ NEW

        # per-unit ratios PY (не храним отдельно – повторяем LY значения)
        avg_sale_per_unit_ratio_py = avg_sale_per_unit_ratio  # ★ NEW
        avg_rent_per_unit_ratio_py = avg_rent_per_unit_ratio  # ★ NEW
        avg_sqm_by_building = _fmean_attr(br_qs, "avg_sqm_sale_ly")  # ★ NEW
        avg_ppsqm_by_building = _fmean_attr(br_qs, "avg_ppsqm_sale_ly")  # ★ NEW
        avg_ppsqm_rent_by_building = _fmean_attr(br_qs, "avg_ppsqm_rent_ly")  # ★ NEW

        avg_sqm_by_building_py = _fmean_attr(br_qs, "avg_sqm_sale_py")  # ★ NEW
        avg_ppsqm_by_building_py = _fmean_attr(br_qs, "avg_ppsqm_sale_py")  # ★ NEW
        avg_ppsqm_rent_by_building_py = _fmean_attr(br_qs, "avg_ppsqm_rent_py")  # ★ NEW
        avg_roi_py = _fmean_attr(br_qs, "roi_py")  # ★ NEW
        # ──────────────────────────────────────────────────────────────
        #           SAVE
        # ──────────────────────────────────────────────────────────────
        with transaction.atomic():
            report, _ = cls.objects.update_or_create(
                bedrooms=bedrooms,
                defaults={
                    # ---------- SALE current (LY raw) ----------------
                    "avg_price": avg_price,
                    "median_price": median_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price_by_building": avg_price_by_building,
                    "avg_exposure_days": avg_exposure_days,
                    # ---------- RENT current (LY raw) ----------------
                    "avg_rent_price": avg_rent_price,
                    "median_rent_price": median_rent_price,
                    "min_rent_price": min_rent_price,
                    "max_rent_price": max_rent_price,
                    "avg_rent_price_by_building": avg_rent_price_by_building,
                    "avg_exposure_rent_days": avg_exposure_rent,
                    # ---------- RATIOS current (LY) ------------------
                    "avg_rent_per_unit_ratio": avg_rent_per_unit_ratio,
                    "avg_sale_per_unit_ratio": avg_sale_per_unit_ratio,
                    "avg_roi": avg_roi,
                    # ---------- SALE LY / PY ------------------------
                    "avg_price_ly": avg_price,
                    "avg_price_py": avg_price_py,  # ★ NEW
                    "median_price_ly": median_price,
                    "median_price_py": median_price_py,  # ★ NEW
                    "min_price_ly": min_price,
                    "min_price_py": min_price_py,  # ★ NEW
                    "max_price_ly": max_price,
                    "max_price_py": max_price_py,  # ★ NEW
                    "count_sale_ly": cnt_sale_ly,
                    "count_sale_py": int(count_sale_py or 0),  # ★ NEW
                    # ---------- RENT LY / PY ------------------------
                    "avg_rent_price_ly": avg_rent_price,
                    "avg_rent_price_py": avg_rent_price_py,  # ★ NEW
                    "median_rent_price_ly": median_rent_price,
                    "median_rent_price_py": median_rent_price_py,  # ★ NEW
                    "min_rent_price_ly": min_rent_price,
                    "min_rent_price_py": min_rent_price_py,  # ★ NEW
                    "max_rent_price_ly": max_rent_price,
                    "max_rent_price_py": max_rent_price_py,  # ★ NEW
                    "count_rent_ly": cnt_rent_ly,
                    "count_rent_py": int(count_rent_py or 0),  # ★ NEW
                    # ---------- RATIOS LY / PY ----------------------
                    "avg_rent_per_unit_ratio_ly": avg_rent_per_unit_ratio,
                    "avg_rent_per_unit_ratio_py": avg_rent_per_unit_ratio_py,  # ★ NEW
                    "avg_sale_per_unit_ratio_ly": avg_sale_per_unit_ratio,
                    "avg_sale_per_unit_ratio_py": avg_sale_per_unit_ratio_py,  # ★ NEW
                    "avg_ppsqm_rent_by_building": avg_ppsqm_rent_by_building,  # ★ NEW
                    "avg_sqm_by_building_py": avg_sqm_by_building_py,  # ★ NEW
                    "avg_ppsqm_by_building_py": avg_ppsqm_by_building_py,  # ★ NEW
                    "avg_ppsqm_rent_by_building_py": avg_ppsqm_rent_by_building_py,  # ★ NEW
                    "avg_roi_py": avg_roi_py,  # ★ NEW
                    # ★ NEW: площадь и цена за кв.м
                    "avg_sqm_by_building": avg_sqm_by_building,  # ★ NEW
                    "avg_ppsqm_by_building": avg_ppsqm_by_building,  # ★ NEW
                },
            )
        return report

    # ------------------------------------------------------------------
    def __str__(self):
        return f"Городской отчёт / {self.get_bedrooms_display()}"


from datetime import timedelta


from django.db.models import DecimalField, FloatField
from django.utils import timezone


class DldBuildingReport(models.Model):
    dld_building = models.ForeignKey(
        DldBuilding, on_delete=models.CASCADE, related_name="reports"
    )
    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES)
    calculated_at = models.DateTimeField(auto_now=True)

    # uniform for any bedroom:
    # total_sqm = FloatField(null=True, blank=True)

    # last year (_ly) metrics
    avg_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_sale_ly = FloatField(null=True, blank=True)
    avg_sqm_rent_ly = FloatField(null=True, blank=True)
    avg_ppsqm_sale_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_ppsqm_rent_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_ly = models.PositiveIntegerField(null=True, blank=True)
    count_rent_ly = models.PositiveIntegerField(null=True, blank=True)
    tx_per_unit_pm_ly = FloatField(null=True, blank=True)
    roi_ly = FloatField(null=True, blank=True)

    # prev year (_py) metrics
    avg_sale_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_rent_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_sale_py = FloatField(null=True, blank=True)
    avg_sqm_rent_py = FloatField(null=True, blank=True)
    avg_ppsqm_sale_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_ppsqm_rent_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_sale_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_sale_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_sale_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_py = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_py = models.PositiveIntegerField(null=True, blank=True)
    count_rent_py = models.PositiveIntegerField(null=True, blank=True)
    tx_per_unit_pm_py = FloatField(null=True, blank=True)
    roi_py = FloatField(null=True, blank=True)

    # last 3 tx
    last_3_sales = models.JSONField(null=True, blank=True)
    last_3_rents = models.JSONField(null=True, blank=True)

    # 15-05 !!!!
    tx_per_unit_pm_ly_rent = models.FloatField(null=True, blank=True)
    tx_per_unit_pm_py_rent = models.FloatField(null=True, blank=True)
    avg_exposure_sale_days = models.FloatField(null=True, blank=True)  # ← NEW
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)  # ← NEW
    avg_sale_per_unit_ratio = models.FloatField(null=True, blank=True)  # ← NEW

    # (аналогичные поля были только для продажи)
    class Meta:
        unique_together = ("dld_building", "bedrooms")

    # ------------------------------------------------------------------ #
    #                        ↓↓↓  ГЛАВНЫЙ МЕТОД  ↓↓↓                      #
    # ------------------------------------------------------------------ #
    @classmethod
    def calculate(cls, dld: "DldBuilding", bedrooms: str) -> "DldBuildingReport | None":
        """
        Пересчитывает ВСЕ метрики для одного здания + комнатности.
        """
        # локальные импорты (чтобы не создавать циклических)
        from .models import MergedTransaction, MergedRentalTransaction

        # === NEW ===  грубый helper (бывший _bedrooms_to_int отсутствовал → None)
        def _bedrooms_to_int(text: str | None) -> int | None:
            """
            'studio' → 0, '1', '1 B/R', '1B/R', '1 bed' → 1  и т. д.
            Возвращает None, если распарсить не удалось.
            """
            if not text:
                return None
            text = str(text).lower().strip()
            if "studio" in text:
                return 0
            match = re.search(r"\d+", text)
            return int(match.group()) if match else None

        # границы дат
        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)
        two_years_ago = today - timedelta(days=730)

        # нормализуем bedrooms
        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None

        # -------------------------------------------------------------- #
        #         БЫСТРАЯ ВЫБОРКА + фильтр по комнатности                #
        # -------------------------------------------------------------- #
        def fetch_tx(model, start: date, end: date):
            qs = model.objects.filter(
                building=dld, date_of_transaction__range=(start, end)
            ).values(
                "pk",
                "transaction_price",
                "sqm",
                "date_of_transaction",
                "period",
                "number_of_rooms",
            )
            out = []
            for rec in qs:
                if rec["transaction_price"] is None or not rec["sqm"]:
                    continue
                if _bedrooms_to_int(rec["number_of_rooms"]) != bed_int:
                    continue
                # ★ FIX: price → float, sqm → float
                rec["transaction_price"] = float(rec["transaction_price"])
                rec["sqm"] = float(rec["sqm"])
                out.append(rec)

            return out

        sale_ly = fetch_tx(MergedTransaction, one_year_ago, today)
        rent_ly = fetch_tx(MergedRentalTransaction, one_year_ago, today)
        sale_py = fetch_tx(
            MergedTransaction, two_years_ago, one_year_ago - timedelta(days=1)
        )
        rent_py = fetch_tx(
            MergedRentalTransaction, two_years_ago, one_year_ago - timedelta(days=1)
        )

        # -------------------------------------------------------------- #
        #           Статистика для любой выборки rows[]                 #
        # -------------------------------------------------------------- #
        def stats(rows):
            if not rows:
                return {
                    "avg_price": None,
                    "median_price": None,
                    "min_price": None,
                    "max_price": None,
                    "avg_sqm": None,
                    "avg_ppsqm": None,
                    "count": 0,
                    "last_3": [],
                    "avg_exposure": None,  # === NEW ===
                }

            prices = [float(r["transaction_price"]) for r in rows]
            sqms = [float(r["sqm"]) for r in rows]

            # --- NEW --- средняя «экспозиция» через поле period ----------
            _period_to_days = {
                "1 week": 7,
                "1 month": 30,
                "3 month": 90,
                "6 month": 180,
                "1 year": 365,
                "2 years": 730,
                "older than 2 years": 1095,
            }
            expos = [
                _period_to_days.get(r["period"], None)
                for r in rows
                if r["period"] in _period_to_days
            ]
            expos = [d for d in expos if d is not None]
            # -------------------------------------------------------------

            return {
                "avg_price": sum(prices) / len(prices),
                "median_price": statistics.median(prices),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_sqm": sum(sqms) / len(sqms),
                "avg_ppsqm": (sum(prices) / sum(sqms)) if sum(sqms) else None,
                "count": len(prices),
                "last_3": [
                    {
                        "price": float(r["transaction_price"]),  #  ← было Decimal
                        "sqm": r["sqm"],
                        "date": r["date_of_transaction"].isoformat(),
                    }
                    for r in sorted(
                        rows, key=lambda x: x["date_of_transaction"], reverse=True
                    )[:3]
                ],
                "avg_exposure": (sum(expos) / len(expos))
                if expos
                else None,  # === NEW ===
            }

        s_ly, r_ly = stats(sale_ly), stats(rent_ly)
        s_py, r_py = stats(sale_py), stats(rent_py)

        # -------------------------------------------------------------- #
        #              Дополнительные метрики per-unit / roi            #
        # -------------------------------------------------------------- #
        total_units = getattr(dld, "total_units", 0) or 0

        # старые (для sales)
        tx_pu_ly_sale = s_ly["count"] / (total_units * 12) if total_units else None
        tx_pu_py_sale = s_py["count"] / (total_units * 12) if total_units else None
        # --- NEW ---  аналогично для аренды
        tx_pu_ly_rent = (
            r_ly["count"] / (total_units * 12) if total_units else None
        )  # === NEW ===
        tx_pu_py_rent = (
            r_py["count"] / (total_units * 12) if total_units else None
        )  # === NEW ===

        def safe_roi(r, s):
            return (
                r["avg_price"] / s["avg_price"]
                if (r["avg_price"] and s["avg_price"])
                else None
            )

        roi_ly = safe_roi(r_ly, s_ly)
        roi_py = safe_roi(r_py, s_py)

        # --- NEW ---  «средняя продажа / юнит» (кол-во продаж к юнитам)
        avg_sale_per_unit_ratio = (
            s_ly["count"] / total_units if total_units else None
        )  # === NEW ===

        # -------------------------------------------------------------- #
        #                    Сохранение / обновление                     #
        # -------------------------------------------------------------- #
        with transaction.atomic():
            report, _ = cls.objects.update_or_create(
                dld_building=dld,
                bedrooms=bedrooms,
                defaults={
                    # ---------------- LAST YEAR ----------------
                    "avg_sale_price_ly": s_ly["avg_price"],
                    "avg_rent_price_ly": r_ly["avg_price"],
                    "avg_sqm_sale_ly": s_ly["avg_sqm"],
                    "avg_sqm_rent_ly": r_ly["avg_sqm"],
                    "avg_ppsqm_sale_ly": s_ly["avg_ppsqm"],
                    "avg_ppsqm_rent_ly": r_ly["avg_ppsqm"],
                    "median_sale_price_ly": s_ly["median_price"],
                    "median_rent_price_ly": r_ly["median_price"],
                    "min_sale_price_ly": s_ly["min_price"],
                    "min_rent_price_ly": r_ly["min_price"],
                    "max_sale_price_ly": s_ly["max_price"],
                    "max_rent_price_ly": r_ly["max_price"],
                    "count_sale_ly": s_ly["count"],
                    "count_rent_ly": r_ly["count"],
                    "tx_per_unit_pm_ly": tx_pu_ly_sale,
                    "tx_per_unit_pm_ly_rent": tx_pu_ly_rent,  # === NEW ===
                    "roi_ly": roi_ly,
                    # ------------- PREVIOUS YEAR --------------
                    "avg_sale_price_py": s_py["avg_price"],
                    "avg_rent_price_py": r_py["avg_price"],
                    "avg_sqm_sale_py": s_py["avg_sqm"],
                    "avg_sqm_rent_py": r_py["avg_sqm"],
                    "avg_ppsqm_sale_py": s_py["avg_ppsqm"],
                    "avg_ppsqm_rent_py": r_py["avg_ppsqm"],
                    "median_sale_price_py": s_py["median_price"],
                    "median_rent_price_py": r_py["median_price"],
                    "min_sale_price_py": s_py["min_price"],
                    "min_rent_price_py": r_py["min_price"],
                    "max_sale_price_py": s_py["max_price"],
                    "max_rent_price_py": r_py["max_price"],
                    "count_sale_py": s_py["count"],
                    "count_rent_py": r_py["count"],
                    "tx_per_unit_pm_py": tx_pu_py_sale,
                    "tx_per_unit_pm_py_rent": tx_pu_py_rent,  # === NEW ===
                    "roi_py": roi_py,
                    # ------------- EXPOSURE + ПРОЧЕЕ ----------
                    "avg_exposure_sale_days": s_ly["avg_exposure"],  # === NEW ===
                    "avg_exposure_rent_days": r_ly["avg_exposure"],  # === NEW ===
                    "avg_sale_per_unit_ratio": avg_sale_per_unit_ratio,  # === NEW ===
                    # ------------- LAST 3 TX ------------------
                    "last_3_sales": s_ly["last_3"],
                    "last_3_rents": r_ly["last_3"],
                },
            )
        return report

    # ------------------------------------------------------------------ #
    #  Публичная утилита — пересчитать всё сразу                         #
    # ------------------------------------------------------------------ #
    @classmethod
    def fill_all(cls):
        from .models import DldBuilding  # локальный импорт, как и раньше

        for dld in DldBuilding.objects.all():
            for key, _ in BEDROOM_CHOICES:
                cls.calculate(dld, key)


class AreaReportDLD(models.Model):
    area = models.ForeignKey(DldArea, on_delete=models.CASCADE, related_name="reports")
    bedrooms = models.CharField(max_length=10, choices=BEDROOM_CHOICES)
    calculated_at = models.DateTimeField(auto_now=True)

    # — показатели по продажам за последний год —
    avg_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_sale_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_sale_ly = FloatField(null=True, blank=True)
    avg_ppsqm_sale_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_ly = models.PositiveIntegerField(null=True, blank=True)

    # — показатели по аренде за последний год —
    avg_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_rent_ly = FloatField(null=True, blank=True)
    avg_ppsqm_rent_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_rent_ly = models.PositiveIntegerField(null=True, blank=True)

    # — группировка по зданиям в районе —
    avg_price_by_building_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_by_building_ly = DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_tx_per_building_ly = FloatField(null=True, blank=True)
    avg_roi_by_building_ly = FloatField(null=True, blank=True)

    # — последние 3 сделки —
    last_3_sales = models.JSONField(null=True, blank=True)
    last_3_rents = models.JSONField(null=True, blank=True)
    # 15-05
    # --- Новые поля по прошлому году (PY) для продажи ---
    avg_sale_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_sale_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_sale_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_sale_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_sale_py = models.FloatField(null=True, blank=True)
    avg_ppsqm_sale_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_sale_py = models.PositiveIntegerField(null=True, blank=True)
    avg_price_by_building_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_price_by_building_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_tx_per_building_py = models.FloatField(null=True, blank=True)
    avg_roi_by_building_py = models.FloatField(null=True, blank=True)

    # --- Новые поля по прошлому году (PY) для аренды ---
    avg_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    median_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    min_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    max_rent_price_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    avg_sqm_rent_py = models.FloatField(null=True, blank=True)
    avg_ppsqm_rent_py = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    count_rent_py = models.PositiveIntegerField(null=True, blank=True)

    # --- Ликвидность аренды ---
    avg_tx_per_building_ly_rent = models.FloatField(null=True, blank=True)
    avg_tx_per_building_py_rent = models.FloatField(null=True, blank=True)

    avg_exposure_sale_days = models.FloatField(null=True, blank=True)  # ← NEW
    avg_exposure_rent_days = models.FloatField(null=True, blank=True)  # ← NEW
    avg_sale_per_unit_ratio = models.FloatField(null=True, blank=True)  # ← NEW

    class Meta:
        unique_together = ("area", "bedrooms")

    #
    # @classmethod
    @classmethod
    def calculate(cls, area: DldArea, bedrooms: str) -> Optional["AreaReportDLD"]:
        """
        Оптимизированный расчёт для одного района и одной комнатности.
        """

        # ──────────────────────────────────────────────────────────────
        # ВСЁ ЧТО НИЖЕ ‒ ВЕСЬ ПЕРЕРАБОТАННЫЙ МЕТОД ЦЕЛИКОМ
        # новые и изменённые строки отмечены «# ★ NEW»
        # ──────────────────────────────────────────────────────────────

        from collections import defaultdict
        from django.utils import timezone
        from datetime import timedelta
        from .models import (
            MergedTransaction,
            MergedRentalTransaction,
            DldBuildingReport,  # ★ NEW
        )
        import statistics  # ★ NEW

        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)

        # 1) нормализуем bedrooms  ("1br"→1, "studio"→0 и т.п.)
        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None

        # 2) —–– СЫРЫЕ ТРАНЗАКЦИИ ЗА ПОСЛЕДНИЙ ГОД (LY) ––––––––––––––
        sale_qs = MergedTransaction.objects.filter(
            area=area, date_of_transaction__gte=one_year_ago
        ).values(
            "transaction_price",
            "sqm",
            "date_of_transaction",
            "building_id",
            "number_of_rooms",
        )
        rent_qs = MergedRentalTransaction.objects.filter(
            area=area, date_of_transaction__gte=one_year_ago
        ).values(
            "transaction_price",
            "sqm",
            "date_of_transaction",
            "building_id",
            "number_of_rooms",
        )

        def _prepare(raw):
            out = []
            for r in raw:
                if (
                    r["transaction_price"] is None
                    or not r["sqm"]
                    or _bedrooms_to_int(str(r["number_of_rooms"])) != bed_int
                ):
                    continue
                out.append(
                    (
                        float(r["transaction_price"]),
                        float(r["sqm"]),
                        r["date_of_transaction"],
                        r["building_id"],
                    )
                )
            return out

        sales_ly = _prepare(sale_qs)
        rents_ly = _prepare(rent_qs)

        # 3) —–– СТАТИСТИКА ПО LY ––––––––––––––––––––––––––––––––––––
        def _stats(rows):
            prices = [p for p, *_ in rows]
            sqms = [s for _, s, *_ in rows]

            return {
                "avg_price": (sum(prices) / len(prices)) if prices else None,
                "median_price": statistics.median(prices) if prices else None,
                "min_price": min(prices) if prices else None,
                "max_price": max(prices) if prices else None,
                "avg_sqm": (sum(sqms) / len(sqms)) if sqms else None,
                "avg_ppsqm": (sum(prices) / sum(sqms)) if prices and sqms else None,
                "count": len(prices),
                "last_3": [
                    {"price": p, "sqm": s, "date": d.isoformat()}
                    for p, s, d, _ in sorted(rows, key=lambda x: x[2], reverse=True)[:3]
                ],
            }

        st_ly = _stats(sales_ly)
        rt_ly = _stats(rents_ly)

        # 4) —–– АГРЕГАЦИЯ ПО ЗДАНИЯМ (LY) –––––––––––––––––––––––––––
        by_building = defaultdict(list)
        for p, *_, bid in sales_ly:
            by_building[bid].append(p)

        avg_by_b_ly = (
            sum(sum(v) / len(v) for v in by_building.values()) / len(by_building)
            if by_building
            else None
        )
        med_by_b_ly = (
            statistics.median([sum(v) / len(v) for v in by_building.values()])
            if by_building
            else None
        )
        avg_tx_b_ly = (
            sum(len(v) for v in by_building.values()) / len(by_building)
            if by_building
            else None
        )
        # ROI по зданиям (LY)
        roi_vals_ly = []
        for bid, sale_prices in by_building.items():
            avg_sale = sum(sale_prices) / len(sale_prices)
            rent_prices_b = [p for p, *_, b in rents_ly if b == bid]
            if rent_prices_b and avg_sale:
                roi_vals_ly.append((sum(rent_prices_b) / len(rent_prices_b)) / avg_sale)
        avg_roi_b_ly = sum(roi_vals_ly) / len(roi_vals_ly) if roi_vals_ly else None

        # 5) —–– ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ИЗ BuildingReport ––––––––––––
        br_building_qs = DldBuildingReport.objects.filter(  # ★ NEW
            dld_building__area=area,  # ★ NEW
            bedrooms=bedrooms,  # ★ NEW
        )  # ★ NEW

        expo_sale_vals = [
            br.avg_exposure_sale_days
            for br in br_building_qs
            if br.avg_exposure_sale_days is not None
        ]  # ★ NEW
        expo_rent_vals = [
            br.avg_exposure_rent_days
            for br in br_building_qs
            if br.avg_exposure_rent_days is not None
        ]  # ★ NEW
        sale_ratio_vals = [
            br.avg_sale_per_unit_ratio
            for br in br_building_qs
            if br.avg_sale_per_unit_ratio is not None
        ]  # ★ NEW

        avg_expo_sale = (
            (sum(expo_sale_vals) / len(expo_sale_vals)) if expo_sale_vals else None
        )  # ★ NEW
        avg_expo_rent = (
            (sum(expo_rent_vals) / len(expo_rent_vals)) if expo_rent_vals else None
        )  # ★ NEW
        avg_sale_ratio = (
            (sum(sale_ratio_vals) / len(sale_ratio_vals)) if sale_ratio_vals else None
        )  # ★ NEW

        # 6) —–– АГРЕГАЦИЯ PREVIOUS-YEAR (PY) ИЗ DldBuildingReport –––
        br_py_qs = br_building_qs  # ★ NEW (alias)

        def _fmean(values):  # ★ NEW
            vals = [float(v) for v in values if v is not None]
            return sum(vals) / len(vals) if vals else None

        def _fmedian(values):  # ★ NEW
            vals = [float(v) for v in values if v is not None]
            return statistics.median(vals) if vals else None

        # --- SALE PY --------------------------------------------------
        sale_avg_vals = [br.avg_sale_price_py for br in br_py_qs]  # ★ NEW
        sale_med_vals = [br.median_sale_price_py for br in br_py_qs]  # ★ NEW
        sale_min_vals = [
            br.min_sale_price_py for br in br_py_qs if br.min_sale_price_py
        ]  # ★ NEW
        sale_max_vals = [
            br.max_sale_price_py for br in br_py_qs if br.max_sale_price_py
        ]  # ★ NEW
        sale_sqm_vals = [br.avg_sqm_sale_py for br in br_py_qs]  # ★ NEW
        sale_ppsqm_vals = [br.avg_ppsqm_sale_py for br in br_py_qs]  # ★ NEW
        sale_cnt_vals = [br.count_sale_py or 0 for br in br_py_qs]  # ★ NEW
        sale_roi_vals = [br.roi_py for br in br_py_qs]  # ★ NEW

        avg_sale_price_py = _fmean(sale_avg_vals)  # ★ NEW
        median_sale_price_py = _fmedian(sale_med_vals)  # ★ NEW
        min_sale_price_py = min(sale_min_vals) if sale_min_vals else None  # ★ NEW
        max_sale_price_py = max(sale_max_vals) if sale_max_vals else None  # ★ NEW
        avg_sqm_sale_py = _fmean(sale_sqm_vals)  # ★ NEW
        avg_ppsqm_sale_py = _fmean(sale_ppsqm_vals)  # ★ NEW
        count_sale_py = sum(sale_cnt_vals)  # ★ NEW
        avg_price_by_building_py = avg_sale_price_py  # ★ NEW
        median_price_by_building_py = _fmedian(sale_avg_vals)  # ★ NEW
        avg_tx_per_building_py = _fmean(sale_cnt_vals)  # ★ NEW
        avg_roi_by_building_py = _fmean(sale_roi_vals)  # ★ NEW

        # --- RENT PY --------------------------------------------------
        rent_avg_vals = [br.avg_rent_price_py for br in br_py_qs]  # ★ NEW
        rent_med_vals = [br.median_rent_price_py for br in br_py_qs]  # ★ NEW
        rent_min_vals = [
            br.min_rent_price_py for br in br_py_qs if br.min_rent_price_py
        ]  # ★ NEW
        rent_max_vals = [
            br.max_rent_price_py for br in br_py_qs if br.max_rent_price_py
        ]  # ★ NEW
        rent_sqm_vals = [br.avg_sqm_rent_py for br in br_py_qs]  # ★ NEW
        rent_ppsqm_vals = [br.avg_ppsqm_rent_py for br in br_py_qs]  # ★ NEW
        rent_cnt_vals = [br.count_rent_py or 0 for br in br_py_qs]  # ★ NEW

        avg_rent_price_py = _fmean(rent_avg_vals)  # ★ NEW
        median_rent_price_py = _fmedian(rent_med_vals)  # ★ NEW
        min_rent_price_py = min(rent_min_vals) if rent_min_vals else None  # ★ NEW
        max_rent_price_py = max(rent_max_vals) if rent_max_vals else None  # ★ NEW
        avg_sqm_rent_py = _fmean(rent_sqm_vals)  # ★ NEW
        avg_ppsqm_rent_py = _fmean(rent_ppsqm_vals)  # ★ NEW
        count_rent_py = sum(rent_cnt_vals)  # ★ NEW
        avg_tx_per_building_py_rent = _fmean(rent_cnt_vals)  # ★ NEW

        # 7) —–– СОХРАНЯЕМ ВСЁ ЗА ОДИН UPDATE_OR_CREATE –––––––––––––––
        report, _ = cls.objects.update_or_create(
            area=area,
            bedrooms=bedrooms,
            defaults={
                # ── LY (как было) ───────────────────────────────────
                "avg_sale_price_ly": st_ly["avg_price"],
                "median_sale_price_ly": st_ly["median_price"],
                "min_sale_price_ly": st_ly["min_price"],
                "max_sale_price_ly": st_ly["max_price"],
                "avg_sqm_sale_ly": st_ly["avg_sqm"],
                "avg_ppsqm_sale_ly": st_ly["avg_ppsqm"],
                "count_sale_ly": st_ly["count"],
                "avg_price_by_building_ly": avg_by_b_ly,
                "median_price_by_building_ly": med_by_b_ly,
                "avg_tx_per_building_ly": avg_tx_b_ly,
                "avg_roi_by_building_ly": avg_roi_b_ly,
                "avg_rent_price_ly": rt_ly["avg_price"],
                "median_rent_price_ly": rt_ly["median_price"],
                "min_rent_price_ly": rt_ly["min_price"],
                "max_rent_price_ly": rt_ly["max_price"],
                "avg_sqm_rent_ly": rt_ly["avg_sqm"],
                "avg_ppsqm_rent_ly": rt_ly["avg_ppsqm"],
                "count_rent_ly": rt_ly["count"],
                "last_3_sales": st_ly["last_3"],
                "last_3_rents": rt_ly["last_3"],
                "avg_exposure_sale_days": avg_expo_sale,
                "avg_exposure_rent_days": avg_expo_rent,
                "avg_sale_per_unit_ratio": avg_sale_ratio,
                # ── PY (★ NEW) ─────────────────────────────────────
                "avg_sale_price_py": avg_sale_price_py,  # ★ NEW
                "median_sale_price_py": median_sale_price_py,  # ★ NEW
                "min_sale_price_py": min_sale_price_py,  # ★ NEW
                "max_sale_price_py": max_sale_price_py,  # ★ NEW
                "avg_sqm_sale_py": avg_sqm_sale_py,  # ★ NEW
                "avg_ppsqm_sale_py": avg_ppsqm_sale_py,  # ★ NEW
                "count_sale_py": count_sale_py,  # ★ NEW
                "avg_price_by_building_py": avg_price_by_building_py,  # ★ NEW
                "median_price_by_building_py": median_price_by_building_py,  # ★ NEW
                "avg_tx_per_building_py": avg_tx_per_building_py,  # ★ NEW
                "avg_roi_by_building_py": avg_roi_by_building_py,  # ★ NEW
                "avg_rent_price_py": avg_rent_price_py,  # ★ NEW
                "median_rent_price_py": median_rent_price_py,  # ★ NEW
                "min_rent_price_py": min_rent_price_py,  # ★ NEW
                "max_rent_price_py": max_rent_price_py,  # ★ NEW
                "avg_sqm_rent_py": avg_sqm_rent_py,  # ★ NEW
                "avg_ppsqm_rent_py": avg_ppsqm_rent_py,  # ★ NEW
                "count_rent_py": count_rent_py,  # ★ NEW
                "avg_tx_per_building_py_rent": avg_tx_per_building_py_rent,  # ★ NEW
            },
        )

        return report

    @classmethod
    def fill_all(cls):
        """Запустить для всех районов и всех типов комнат."""
        for area in DldArea.objects.all():
            for key, _ in BEDROOM_CHOICES:
                cls.calculate(area, key)

    def __str__(self):
        return f"Отчёт по {self.area} / {self.get_bedrooms_display()}"

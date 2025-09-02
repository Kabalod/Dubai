# realty/reports/management/commands/rebuild_city_report.py
import statistics
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from realty.reports.utils import _bedrooms_to_int  # ваш helper

# локальные импорты, чтобы избежать циклов
from realty.pfimport.models import PFListSale, PFListRent
from realty.reports.models import CityReport, DldBuildingReport


class Command(BaseCommand):
    """
    Пересчитывает один CityReport по Дубаю (LY / PY + средние по зданиям).

    Пример:
        python manage.py rebuild_city_report 2br
        python manage.py rebuild_city_report studio --dry-run
    """

    help = "Полный пересчёт CityReport для указанной комнатности."

    # ------------------------------------------------------------------ CLI

    def add_arguments(self, parser):
        parser.add_argument(
            "bedrooms",
            help="Комнатность: studio | 1br | 2br | 3br | …",
        )
        parser.add_argument("--dry-run", action="store_true")

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _safe_mean(seq):
        return (sum(seq) / len(seq)) if seq else None

    @staticmethod
    def _safe_median(seq):
        return statistics.median(seq) if seq else None

    @staticmethod
    def _stat(nums):
        """mean, median, min, max, count (floats)"""
        if not nums:
            return None, None, None, None, 0
        return (
            sum(nums) / len(nums),
            statistics.median(nums),
            min(nums),
            max(nums),
            len(nums),
        )

    # ------------------------------------------------------------------ main

    def handle(self, *args, **opts):
        bedrooms = opts["bedrooms"]
        dry = opts["dry_run"]

        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            self.stderr.write(self.style.ERROR("Неизвестная комнатность"))
            return

        today = date.today()
        one_year_ago = today - timedelta(days=365)
        start_py = today - timedelta(days=730)
        end_py = one_year_ago - timedelta(days=1)

        # ---------------- RAW PF-объявления (LY) -----------------------
        sale_ly = [
            float(p)
            for p in PFListSale.objects.filter(
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        rent_ly = [
            float(p)
            for p in PFListRent.objects.filter(
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]

        # если за последний год нет ни продажи, ни аренды ‒ отчёт не нужен
        if not sale_ly and not rent_ly:
            self.stdout.write(
                self.style.WARNING(f"[SKIPPED] {bedrooms}: нет объявлений за LY")
            )
            return

        (
            avg_price,
            med_price,
            min_price,
            max_price,
            cnt_sale_ly,
        ) = self._stat(sale_ly)
        (
            avg_rent,
            med_rent,
            min_rent,
            max_rent,
            cnt_rent_ly,
        ) = self._stat(rent_ly)

        # ---------------- RAW PF-объявления (PY) -----------------------
        sale_py = [
            float(p)
            for p in PFListSale.objects.filter(
                bedrooms__iexact=str(bed_int),
                added_on__range=(start_py, end_py),
            ).values_list("price", flat=True)
            if p
        ]
        rent_py = [
            float(p)
            for p in PFListRent.objects.filter(
                bedrooms__iexact=str(bed_int),
                added_on__range=(start_py, end_py),
            ).values_list("price", flat=True)
            if p
        ]

        (
            avg_price_py,
            med_price_py,
            min_price_py,
            max_price_py,
            cnt_sale_py,
        ) = self._stat(sale_py)
        (
            avg_rent_py,
            med_rent_py,
            min_rent_py,
            max_rent_py,
            cnt_rent_py,
        ) = self._stat(rent_py)

        # ---------------- Агрегаты DldBuildingReport ------------------
        br_qs = DldBuildingReport.objects.filter(bedrooms=bedrooms)

        def mean_attr(attr):
            vals = [
                float(getattr(r, attr)) for r in br_qs if getattr(r, attr) is not None
            ]
            return self._safe_mean(vals)

        def median_attr(attr):
            vals = [
                float(getattr(r, attr)) for r in br_qs if getattr(r, attr) is not None
            ]
            return self._safe_median(vals)

        # LY (по зданиям)
        avg_price_by_building = mean_attr("avg_sale_price_ly")
        avg_rent_by_building = mean_attr("avg_rent_price_ly")
        avg_exposure_days = mean_attr("avg_exposure_sale_days")
        avg_exposure_rent_days = mean_attr("avg_exposure_rent_days")
        avg_sale_per_unit_ratio = mean_attr("avg_sale_per_unit_ratio")
        avg_ppsqm_by_building = mean_attr("avg_ppsqm_sale_ly")
        avg_ppsqm_rent_by_building = mean_attr("avg_ppsqm_rent_ly")
        avg_sqm_by_building = mean_attr("avg_sqm_sale_ly")
        avg_rent_per_unit_ratio = self._safe_mean(
            [(r.tx_per_unit_pm_ly_rent or 0) * 12 for r in br_qs]
        )
        avg_roi = mean_attr("roi_ly")

        # PY (по зданиям)
        avg_price_by_building_py = mean_attr("avg_sale_price_py")
        avg_rent_by_building_py = mean_attr("avg_rent_price_py")
        avg_ppsqm_by_building_py = mean_attr("avg_ppsqm_sale_py")
        avg_ppsqm_rent_by_building_py = mean_attr("avg_ppsqm_rent_py")
        avg_sqm_by_building_py = mean_attr("avg_sqm_sale_py")
        avg_roi_py = mean_attr("roi_py")
        # per-unit ratios: берём те же значения (отдельно не храните)
        avg_sale_per_unit_ratio_py = avg_sale_per_unit_ratio
        avg_rent_per_unit_ratio_py = avg_rent_per_unit_ratio

        if dry:
            self.stdout.write(
                f"[DRY-RUN] {bedrooms}: sale={cnt_sale_ly}, rent={cnt_rent_ly}, "
                f"BReports={br_qs.count()}"
            )
            return

        # ---------------- SAVE / UPDATE -------------------------------
        with transaction.atomic():
            obj, created = CityReport.objects.update_or_create(
                bedrooms=bedrooms,
                defaults={
                    # ------ SALE current (LY, raw) ------
                    "avg_price": avg_price,
                    "median_price": med_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price_by_building": avg_price_by_building,
                    "avg_exposure_days": avg_exposure_days,
                    # ------ RENT current ---------------
                    "avg_rent_price": avg_rent,
                    "median_rent_price": med_rent,
                    "min_rent_price": min_rent,
                    "max_rent_price": max_rent,
                    "avg_rent_price_by_building": avg_rent_by_building,
                    "avg_exposure_rent_days": avg_exposure_rent_days,
                    # ------ RATIOS current -------------
                    "avg_sale_per_unit_ratio": avg_sale_per_unit_ratio,
                    "avg_rent_per_unit_ratio": avg_rent_per_unit_ratio,
                    "avg_roi": avg_roi,
                    # ------ SALE LY / PY ---------------
                    "avg_price_ly": avg_price,
                    "avg_price_py": avg_price_py,
                    "median_price_ly": med_price,
                    "median_price_py": med_price_py,
                    "min_price_ly": min_price,
                    "min_price_py": min_price_py,
                    "max_price_ly": max_price,
                    "max_price_py": max_price_py,
                    "count_sale_ly": cnt_sale_ly,
                    "count_sale_py": cnt_sale_py,
                    # ------ RENT LY / PY ---------------
                    "avg_rent_price_ly": avg_rent,
                    "avg_rent_price_py": avg_rent_py,
                    "median_rent_price_ly": med_rent,
                    "median_rent_price_py": med_rent_py,
                    "min_rent_price_ly": min_rent,
                    "min_rent_price_py": min_rent_py,
                    "max_rent_price_ly": max_rent,
                    "max_rent_price_py": max_rent_py,
                    "count_rent_ly": cnt_rent_ly,
                    "count_rent_py": cnt_rent_py,
                    # ------ RATIOS LY / PY -------------
                    "avg_sale_per_unit_ratio_ly": avg_sale_per_unit_ratio,
                    "avg_sale_per_unit_ratio_py": avg_sale_per_unit_ratio_py,
                    "avg_rent_per_unit_ratio_ly": avg_rent_per_unit_ratio,
                    "avg_rent_per_unit_ratio_py": avg_rent_per_unit_ratio_py,
                    # ------ NEW sqm / ppsqm ------------
                    "avg_sqm_by_building": avg_sqm_by_building,
                    "avg_ppsqm_by_building": avg_ppsqm_by_building,
                    "avg_ppsqm_rent_by_building": avg_ppsqm_rent_by_building,
                    "avg_sqm_by_building_py": avg_sqm_by_building_py,
                    "avg_ppsqm_by_building_py": avg_ppsqm_by_building_py,
                    "avg_ppsqm_rent_by_building_py": avg_ppsqm_rent_by_building_py,
                    # ------ ROI PY ---------------------
                    "avg_roi_py": avg_roi_py,
                },
            )

        action = "создан" if created else "обновлён"
        self.stdout.write(self.style.SUCCESS(f"CityReport {bedrooms} {action}."))

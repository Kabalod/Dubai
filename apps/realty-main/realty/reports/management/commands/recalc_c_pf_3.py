# realty/reports/management/commands/rebuild_city_report_pf.py
import statistics
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from realty.pfimport.models import PFListSale, PFListRent
from realty.reports.models import CityReportPF, BuildingReport
from realty.reports.utils import _bedrooms_to_int


class Command(BaseCommand):
    """
    Пересчитывает один CityReportPF.

    Пример:
        python manage.py rebuild_city_report_pf 2br
        python manage.py rebuild_city_report_pf 1br --dry-run
    """

    help = "Пересчитать одиночный CityReportPF (по городским данным)."

    # ------------------------------------------------------------------ CLI

    def add_arguments(self, parser):
        parser.add_argument(
            "bedrooms",
            help="Комнатность (studio | 1br | 2br …)",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Только вывод, без записи в БД"
        )

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _safe(fn, seq):
        return fn(seq) if seq else None

    @staticmethod
    def _stat(nums):
        """mean, median, min, max, count — либо None/0."""
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
        start_ly = today - timedelta(days=365)
        start_py = today - timedelta(days=730)
        end_py = start_ly - timedelta(days=1)

        # ------------------------ SALE ---------------------------------
        sale_ly = [
            float(p)
            for p in PFListSale.objects.filter(
                bedrooms__iexact=str(bed_int), added_on__range=(start_ly, today)
            ).values_list("price", flat=True)
            if p
        ]
        sale_py = [
            float(p)
            for p in PFListSale.objects.filter(
                bedrooms__iexact=str(bed_int), added_on__range=(start_py, end_py)
            ).values_list("price", flat=True)
            if p
        ]
        (
            avg_sale,
            med_sale,
            min_sale,
            max_sale,
            cnt_sale_ly,
        ) = self._stat(sale_ly)
        (
            avg_sale_py,
            med_sale_py,
            min_sale_py,
            max_sale_py,
            cnt_sale_py,
        ) = self._stat(sale_py)

        # ------------------------ RENT ---------------------------------
        rent_ly = [
            float(p)
            for p in PFListRent.objects.filter(
                bedrooms__iexact=str(bed_int), added_on__range=(start_ly, today)
            ).values_list("price", flat=True)
            if p
        ]
        rent_py = [
            float(p)
            for p in PFListRent.objects.filter(
                bedrooms__iexact=str(bed_int), added_on__range=(start_py, end_py)
            ).values_list("price", flat=True)
            if p
        ]
        (
            avg_rent,
            med_rent,
            min_rent,
            max_rent,
            cnt_rent_ly,
        ) = self._stat(rent_ly)
        (
            avg_rent_py,
            med_rent_py,
            min_rent_py,
            max_rent_py,
            cnt_rent_py,
        ) = self._stat(rent_py)

        # пропуск, если за LY нет объявлений вовсе
        if cnt_sale_ly == 0 and cnt_rent_ly == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"[SKIPPED] {bedrooms}: нет объявлений за последний год"
                )
            )
            return

        # -------- агрегаты из BuildingReport ---------------------------
        br_qs = BuildingReport.objects.filter(bedrooms=bedrooms)

        sale_build = [float(b.avg_sale_price) for b in br_qs if b.avg_sale_price]
        rent_build = [float(b.avg_rent_price) for b in br_qs if b.avg_rent_price]

        avg_sale_by_build = self._safe(statistics.fmean, sale_build)
        avg_rent_by_build = self._safe(statistics.fmean, rent_build)

        expo_sale = [
            b.avg_exposure_sale_days for b in br_qs if b.avg_exposure_sale_days
        ]
        expo_rent = [
            b.avg_exposure_rent_days for b in br_qs if b.avg_exposure_rent_days
        ]
        avg_expo_sale = self._safe(statistics.fmean, expo_sale)
        avg_expo_rent = self._safe(statistics.fmean, expo_rent)

        sale_ratios = [b.sale_per_unit_ratio for b in br_qs if b.sale_per_unit_ratio]
        rent_ratios = [b.rent_per_unit_ratio for b in br_qs if b.rent_per_unit_ratio]

        avg_sale_ratio = self._safe(statistics.fmean, sale_ratios)
        avg_rent_ratio = self._safe(statistics.fmean, rent_ratios)
        avg_roi = self._safe(statistics.fmean, [b.roi for b in br_qs if b.roi])

        if dry:
            self.stdout.write(
                f"[DRY-RUN] {bedrooms}: sale={cnt_sale_ly}, rent={cnt_rent_ly}"
            )
            return

        # ------------------- SAVE / UPDATE -----------------------------
        with transaction.atomic():
            obj, created = CityReportPF.objects.update_or_create(
                bedrooms=bedrooms,
                defaults={
                    # SALE current
                    "avg_price": avg_sale,
                    "median_price": med_sale,
                    "min_price": min_sale,
                    "max_price": max_sale,
                    "avg_price_by_building": avg_sale_by_build,
                    "avg_exposure_days": avg_expo_sale,
                    # RENT current
                    "avg_rent_price": avg_rent,
                    "median_rent_price": med_rent,
                    "min_rent_price": min_rent,
                    "max_rent_price": max_rent,
                    "avg_rent_price_by_building": avg_rent_by_build,
                    "avg_exposure_rent_days": avg_expo_rent,
                    # RATIOS current
                    "avg_sale_per_unit_ratio": avg_sale_ratio,
                    "avg_rent_per_unit_ratio": avg_rent_ratio,
                    "avg_roi": avg_roi,
                    # SALE LY / PY
                    "avg_price_ly": avg_sale,
                    "avg_price_py": avg_sale_py,
                    "median_price_ly": med_sale,
                    "median_price_py": med_sale_py,
                    "min_price_ly": min_sale,
                    "min_price_py": min_sale_py,
                    "max_price_ly": max_sale,
                    "max_price_py": max_sale_py,
                    "count_sale_ly": cnt_sale_ly,
                    "count_sale_py": cnt_sale_py,
                    # RENT LY / PY
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
                    # RATIOS LY / PY (здесь берём те же, что и current,
                    # если нужны отдельные расчёты – замените)
                    "avg_sale_per_unit_ratio_ly": avg_sale_ratio,
                    "avg_sale_per_unit_ratio_py": avg_sale_ratio,
                    "avg_rent_per_unit_ratio_ly": avg_rent_ratio,
                    "avg_rent_per_unit_ratio_py": avg_rent_ratio,
                },
            )

        action = "создан" if created else "обновлён"
        self.stdout.write(self.style.SUCCESS(f"CityReportPF {bedrooms} {action}."))

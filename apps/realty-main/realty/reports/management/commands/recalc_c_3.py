# realty/reports/management/commands/rebuild_city_reports.py
import statistics
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from realty.pfimport.models import PFListSale, PFListRent
from realty.reports.models import BuildingReport, CityReportPF
from realty.reports.utils import _bedrooms_to_int


class Command(BaseCommand):
    """Пересчитать CityReportPF для каждой комнатности."""

    help = "Пересчитывает CityReportPF (городские отчёты) без вызова calculate()."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bedrooms",
            nargs="*",
            default=["studio", "1br", "2br", "3br", "4br", "5br"],
            help="Перечень комнатностей",
        )
        parser.add_argument("--dry-run", action="store_true")

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _safe(fn, seq):
        return fn(seq) if seq else None

    # ------------------------------------------------------------------ handle

    def handle(self, *args, **opts):
        beds = opts["bedrooms"]
        dry = opts["dry_run"]

        processed = created = updated = skipped = 0

        for br in beds:
            status, reason = self.rebuild(br, dry)
            processed += 1
            if status is None:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"[SKIPPED] {br}: {reason}"))
            elif status is True:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ City done. Tried {processed}, created {created}, "
                f"updated {updated}, skipped {skipped}"
            )
        )

    # ------------------------------------------------------------------ core

    def rebuild(self, bedrooms, dry):
        today = date.today()
        start_ly = today - timedelta(days=365)
        start_py = today - timedelta(days=730)
        end_py = start_ly - timedelta(days=1)

        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None, "не удалось определить комнатность"

        # helper: statistics over list
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

        # ---------------- SALE -----------------------------------------
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
            avg_price,
            med_price,
            min_price,
            max_price,
            cnt_sale_ly,
        ) = stat(sale_ly)
        (
            avg_price_py,
            med_price_py,
            min_price_py,
            max_price_py,
            cnt_sale_py,
        ) = stat(sale_py)

        # ---------------- RENT -----------------------------------------
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
        ) = stat(rent_ly)
        (
            avg_rent_py,
            med_rent_py,
            min_rent_py,
            max_rent_py,
            cnt_rent_py,
        ) = stat(rent_py)

        if cnt_sale_ly == 0 and cnt_rent_ly == 0:
            return None, "нет объявлений за последний год"

        # ---------- metrics from BuildingReport ------------------------
        br_qs = BuildingReport.objects.filter(bedrooms=bedrooms)

        sale_build = [float(b.avg_sale_price) for b in br_qs if b.avg_sale_price]
        rent_build = [float(b.avg_rent_price) for b in br_qs if b.avg_rent_price]

        avg_price_by_build = self._safe(statistics.fmean, sale_build)
        avg_rent_by_build = self._safe(statistics.fmean, rent_build)

        expos_sale = [
            b.avg_exposure_sale_days for b in br_qs if b.avg_exposure_sale_days
        ]
        expos_rent = [
            b.avg_exposure_rent_days for b in br_qs if b.avg_exposure_rent_days
        ]
        avg_expo_sale = self._safe(statistics.fmean, expos_sale)
        avg_expo_rent = self._safe(statistics.fmean, expos_rent)

        sale_ratios = [b.sale_per_unit_ratio for b in br_qs if b.sale_per_unit_ratio]
        rent_ratios = [b.rent_per_unit_ratio for b in br_qs if b.rent_per_unit_ratio]

        avg_sale_ratio = self._safe(statistics.fmean, sale_ratios)
        avg_rent_ratio = self._safe(statistics.fmean, rent_ratios)
        avg_roi = self._safe(statistics.fmean, [b.roi for b in br_qs if b.roi])

        if dry:
            self.stdout.write(
                f"[DRY-RUN] City/{bedrooms}: sale={cnt_sale_ly}, rent={cnt_rent_ly}"
            )
            return True, ""

        # ---------------- save/update ----------------------------------
        with transaction.atomic():
            obj, created = CityReportPF.objects.update_or_create(
                bedrooms=bedrooms,
                defaults={
                    # ------ SALE current ------
                    "avg_price": avg_price,
                    "median_price": med_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price_by_building": avg_price_by_build,
                    "avg_exposure_days": avg_expo_sale,
                    # ------ RENT current ------
                    "avg_rent_price": avg_rent,
                    "median_rent_price": med_rent,
                    "min_rent_price": min_rent,
                    "max_rent_price": max_rent,
                    "avg_rent_price_by_building": avg_rent_by_build,
                    "avg_exposure_rent_days": avg_expo_rent,
                    # ------ ratios ------
                    "avg_sale_per_unit_ratio": avg_sale_ratio,
                    "avg_rent_per_unit_ratio": avg_rent_ratio,
                    "avg_roi": avg_roi,
                    # ------ LY / PY ------
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
                    "avg_sale_per_unit_ratio_ly": avg_sale_ratio,
                    "avg_sale_per_unit_ratio_py": avg_sale_ratio,  # PY временно = текущ.
                    "avg_rent_per_unit_ratio_ly": avg_rent_ratio,
                    "avg_rent_per_unit_ratio_py": avg_rent_ratio,  # PY временно = текущ.
                },
            )
        return created, ""

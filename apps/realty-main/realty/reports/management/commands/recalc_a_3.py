# realty/reports/management/commands/rebuild_area_reports.py
import statistics
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from realty.pfimport.models import PFListSale, PFListRent, Area
from realty.reports.models import BuildingReport, AreaReport
from realty.reports.utils import _bedrooms_to_int, ROOM_MAPPING


class Command(BaseCommand):
    """Пересчитать AreaReport без вызова AreaReport.calculate()."""

    help = (
        "Пересчитывает AreaReport для всех Area / bedrooms. "
        "Для пропущенных отчётов печатает причину."
    )

    # ------------------------------------------------------------------ CLI

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, help="ID района (пересчитать только его)")
        parser.add_argument(
            "--bedrooms",
            nargs="*",
            default=["studio", "1br", "2br", "3br", "4br", "5br"],
            help="Перечень комнатностей",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только вывод, без сохранения в БД",
        )

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _safe(fn, seq):
        return fn(seq) if seq else None

    # ------------------------------------------------------------------ handle

    def handle(self, *args, **opts):
        qs = Area.objects.all()
        if opts["id"]:
            qs = qs.filter(pk=opts["id"])

        beds = opts["bedrooms"]
        one_year_ago = timezone.now() - timedelta(days=365)

        processed = created = updated = skipped = 0

        for area in qs.iterator():
            for br in beds:
                status, reason = self.rebuild(area, br, one_year_ago, opts["dry_run"])
                processed += 1
                if status is None:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"[SKIPPED] {area.pk}/{br}: {reason}")
                    )
                elif status is True:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Areas done. Tried {processed}, created {created}, "
                f"updated {updated}, skipped {skipped}"
            )
        )

    # ------------------------------------------------------------------ core

    def rebuild(self, area, bedrooms, one_year_ago, dry):
        """Return (status, reason)."""

        bed_int = _bedrooms_to_int(bedrooms)
        if bed_int is None:
            return None, "не удалось определить комнатность"

        # ---------- объявления SALE / RENT -----------------------------
        sale_prices = [
            float(p)
            for p in PFListSale.objects.filter(
                building__area=area,
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        rent_prices = [
            float(p)
            for p in PFListRent.objects.filter(
                building__area=area,
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]

        if not sale_prices and not rent_prices:
            return None, "нет объявлений за последний год"

        # ---------------- агрегаты по объявлениям ----------------------
        avg_sale_all = self._safe(statistics.fmean, sale_prices)
        avg_rent_all = self._safe(statistics.fmean, rent_prices)

        med_sale = self._safe(statistics.median, sale_prices)
        med_rent = self._safe(statistics.median, rent_prices)

        min_sale = self._safe(min, sale_prices)
        max_sale = self._safe(max, sale_prices)
        min_rent = self._safe(min, rent_prices)
        max_rent = self._safe(max, rent_prices)

        # ---------- агрегаты «по зданиям» ------------------------------
        br_qs = BuildingReport.objects.filter(building__area=area, bedrooms=bedrooms)

        sale_build = [float(r.avg_sale_price) for r in br_qs if r.avg_sale_price]
        rent_build = [float(r.avg_rent_price) for r in br_qs if r.avg_rent_price]

        avg_sale_by_build = self._safe(statistics.fmean, sale_build)
        avg_rent_by_build = self._safe(statistics.fmean, rent_build)

        # ---------- ratios / exposure ----------------------------------
        sale_ratios = [r.sale_per_unit_ratio for r in br_qs if r.sale_per_unit_ratio]
        rent_ratios = [r.rent_per_unit_ratio for r in br_qs if r.rent_per_unit_ratio]
        rois = [r.roi for r in br_qs if r.roi is not None]

        avg_sale_ratio = self._safe(statistics.fmean, sale_ratios)
        avg_rent_ratio = self._safe(statistics.fmean, rent_ratios)
        avg_roi = self._safe(statistics.fmean, rois)

        expo_sale = [
            r.avg_exposure_sale_days for r in br_qs if r.avg_exposure_sale_days
        ]
        expo_rent = [
            r.avg_exposure_rent_days for r in br_qs if r.avg_exposure_rent_days
        ]
        avg_expo_sale = self._safe(statistics.fmean, expo_sale)
        avg_expo_rent = self._safe(statistics.fmean, expo_rent)

        if dry:
            self.stdout.write(
                f"[DRY-RUN] Area {area.pk}/{bedrooms}: "
                f"sale={len(sale_prices)}, rent={len(rent_prices)}"
            )
            return True, ""

        # ---------------- save/update ----------------------------------
        with transaction.atomic():
            obj, created = AreaReport.objects.update_or_create(
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
                    "avg_exposure_sale_days": avg_expo_sale,
                    "avg_exposure_rent_days": avg_expo_rent,
                    "avg_sale_per_unit_ratio": avg_sale_ratio,
                    "avg_rent_per_unit_ratio": avg_rent_ratio,
                    "avg_roi": avg_roi,
                },
            )
        return created, ""

import json
import statistics
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from realty.pfimport.models import (
    Building,
    PFListSale,
    PFListRent,
)
from realty.reports.models import BuildingReport
from realty.reports.utils import (
    get_room_int_and_units_2 as get_room_int_and_units,  # helper
)


class Command(BaseCommand):
    """Rebuilds BuildingReport objects for every Building / bedrooms pair.

    *Does not* rely on ``BuildingReport.calculate`` – all statistics are
    computed inline.  For every skipped report a human‑readable reason is printed.
    """

    help = (
        "Пересчитывает BuildingReport для всех зданий и всех заданных комнатностей "
        "без использования метода BuildingReport.calculate()."
    )

    # ---------------------------------------------------------------------
    # CLI arguments
    # ---------------------------------------------------------------------

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            type=int,
            help="ID конкретного здания (если нужно пересчитать только его)",
        )
        parser.add_argument(
            "--bedrooms",
            nargs="*",
            default=["studio", "1br", "2br", "3br", "4br", "5br"],
            help="Список комнатностей (по умолчанию: studio 1br 2br 3br 4br 5br)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только вывод, без сохранения в БД",
        )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _safe(fn, seq):
        return fn(seq) if seq else None

    # ---------------------------------------------------------------------
    # Entry point
    # ---------------------------------------------------------------------

    def handle(self, *args, **opts):
        qs = Building.objects.all().select_related("dld_building")
        if opts["id"]:
            qs = qs.filter(pk=opts["id"])

        bedrooms_list = opts["bedrooms"]
        now = timezone.now()
        one_year_ago = now - timedelta(days=365)

        processed = created = updated = skipped = 0

        for building in qs.iterator(chunk_size=200):
            if not building.dld_building:
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIPPED] building {building.pk}: нет dld_building"
                    )
                )
                skipped += len(bedrooms_list)
                continue

            for br in bedrooms_list:
                status, reason = self.recalculate_for(
                    building, br, one_year_ago, opts["dry_run"]
                )
                processed += 1

                if status is None:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"[SKIPPED] {building.pk}/{br}: {reason}")
                    )
                elif status is True:
                    created += 1
                else:  # False – updated
                    updated += 1

        # --- summary ----------------------------------------------------
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Готово!\n"
                f"Попыток расчёта:   {processed}\n"
                f"Создано отчётов:   {created}\n"
                f"Обновлено отчётов: {updated}\n"
                f"Пропущено:         {skipped}"
            )
        )

    # ---------------------------------------------------------------------
    # Per‑building logic
    # ---------------------------------------------------------------------

    def recalculate_for(self, building, bedrooms, one_year_ago, dry_run=False):
        """Return tuple ``(status, reason)``:

        * ``status`` — ``None`` (skipped), ``True`` (created) or ``False`` (updated)
        * ``reason`` — short human‑readable explanation for skipped cases;
          an empty string when the report *was* produced.
        """

        # --- room int & units ------------------------------------------
        bed_int, units = get_room_int_and_units(building, bedrooms)
        if bed_int is None:
            return None, "не удалось определить комнатность"
        if units in (None, 0):
            return None, "units = 0 / нет юнитов данной комнатности"

        dld = building.dld_building
        total_units = dld.total_units or 0

        # --- rooms_count JSON ------------------------------------------
        try:
            rooms_count_json = json.loads(dld.arabic_name or "{}").get(
                "rooms_count", {}
            )
        except (TypeError, ValueError):
            rooms_count_json = {}

        # ---------- SALE -------------------------------------------------
        sale_prices = [
            float(p)
            for p in PFListSale.objects.filter(
                building=building,
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        sale_cnt = len(sale_prices)
        avg_sale = self._safe(statistics.fmean, sale_prices)
        median_sale = self._safe(statistics.median, sale_prices)
        min_sale = self._safe(min, sale_prices)
        max_sale = self._safe(max, sale_prices)
        avg_expo_sale = (
            building.sum_exposure_sale_days / building.numbers_of_processed_sale_ads
            if building.numbers_of_processed_sale_ads
            else None
        )
        sale_per_unit = sale_cnt / units if units else None

        # ---------- RENT -------------------------------------------------
        rent_prices = [
            float(p)
            for p in PFListRent.objects.filter(
                building=building,
                bedrooms__iexact=str(bed_int),
                added_on__gte=one_year_ago,
            ).values_list("price", flat=True)
            if p
        ]
        rent_cnt = len(rent_prices)
        avg_rent = self._safe(statistics.fmean, rent_prices)
        median_rent = self._safe(statistics.median, rent_prices)
        min_rent = self._safe(min, rent_prices)
        max_rent = self._safe(max, rent_prices)
        avg_expo_rent = (
            building.sum_exposure_rent_days / building.numbers_of_processed_rent_ads
            if building.numbers_of_processed_rent_ads
            else None
        )
        rent_per_unit = rent_cnt / units if units else None

        # ---------- ROI --------------------------------------------------
        roi = (avg_rent / avg_sale) if (avg_rent and avg_sale) else None

        # если после всех вычислений нет ни одной метрики — пропускаем
        if all(m is None for m in (avg_sale, median_sale, avg_rent, median_rent, roi)):
            return None, "нет цен за последний год"

        if dry_run:
            self.stdout.write(
                f"[DRY‑RUN] {building.pk}/{bedrooms}: "
                f"sale={sale_cnt}, rent={rent_cnt}, roi={roi}"
            )
            return True, ""

        # ---------- save/update -----------------------------------------
        with transaction.atomic():
            report, created = BuildingReport.objects.update_or_create(
                building=building,
                bedrooms=bedrooms,
                defaults={
                    # ---- sale ----
                    "avg_sale_price": avg_sale,
                    "median_sale_price": median_sale,
                    "min_sale_price": min_sale,
                    "max_sale_price": max_sale,
                    "sale_count": sale_cnt,
                    "avg_exposure_sale_days": avg_expo_sale,
                    "sale_per_unit_ratio": sale_per_unit,
                    # ---- rent ----
                    "avg_rent_price": avg_rent,
                    "median_rent_price": median_rent,
                    "min_rent_price": min_rent,
                    "max_rent_price": max_rent,
                    "rent_count": rent_cnt,
                    "avg_exposure_rent_days": avg_expo_rent,
                    "rent_per_unit_ratio": rent_per_unit,
                    # ---- misc ----
                    "type_of_rooms_in": rooms_count_json,
                    "total_units": total_units,
                    "roi": roi,
                    "area": building.area,
                    "dld_building": dld,
                    "units": units,
                },
            )
        return created, ""

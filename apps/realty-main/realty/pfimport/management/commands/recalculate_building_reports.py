# realty/reports/management/commands/recalculate_building_reports.py
from django.core.management.base import BaseCommand
from django.db import transaction

from realty.pfimport.models import Building
from realty.reports.models import BuildingReport, BEDROOM_CHOICES


class Command(BaseCommand):
    help = (
        "Пересчитывает BuildingReport для всех (или выбранных) зданий и типов спален. "
        "По-умолчанию проходит последовательно по всем Building с привязкой к DLD."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--building",
            type=int,
            help="ID одного конкретного Building; если не указан — берём все.",
        )
        parser.add_argument(
            "--bedrooms",
            type=str,
            choices=[key for key, _ in BEDROOM_CHOICES],
            help="Ограничить пересчёт одним типом спален (studio, 1br, …).",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        # ── формируем выборку зданий ───────────────────────────────────
        buildings_qs = Building.objects.exclude(dld_building__isnull=True)
        if options.get("building"):
            buildings_qs = buildings_qs.filter(pk=options["building"])

        # ── набор комнатностей ─────────────────────────────────────────
        bedrooms_list = (
            [options["bedrooms"]]
            if options.get("bedrooms")
            else [key for key, _ in BEDROOM_CHOICES]
        )

        total_tasks = buildings_qs.count() * len(bedrooms_list)
        processed = 0

        self.stdout.write(
            f"Запускаю пересчёт {total_tasks} задач "
            f"({buildings_qs.count()} зданий × {len(bedrooms_list)} типов спален)…"
        )

        # ── поочерёдный расчёт ─────────────────────────────────────────
        for building in buildings_qs.iterator():
            for br_key in bedrooms_list:
                try:
                    with transaction.atomic():
                        report = BuildingReport.calculate(building, br_key)

                    msg = (
                        self.style.SUCCESS("OK")
                        if report
                        else self.style.WARNING("SKIP")
                    )
                    self.stdout.write(f"{msg}: {building} / {br_key}")
                except Exception as exc:  # pylint: disable=broad-except
                    self.stderr.write(
                        self.style.ERROR(f"ERROR: {building} / {br_key} — {exc}")
                    )

                processed += 1
                # короткий индикатор прогресса
                self.stdout.write(f"Progress: {processed}/{total_tasks}", ending="\r")

        self.stdout.write(self.style.SUCCESS("✓ Готово"))

from __future__ import annotations

from typing import Iterable, Mapping

from django.core.management.base import BaseCommand
from django.db import transaction

from realty.pfimport.models import Building, Area as PF_Area
from realty.main.models import DldBuilding, Area as DLD_Area
from realty.reports.models import (  # импортируем отчёты
    BuildingReport,
    AreaReport,
    CityReportPF,
    CityReport,
    DldBuildingReport,
    AreaReportDLD,
    BEDROOM_CHOICES,
)

# ----------------------------------------------------------------------
#                      ↓↓↓  СЛУЖЕБНЫЕ НАСТРОЙКИ  ↓↓↓
# ----------------------------------------------------------------------
BR_CHOICES = [key for key, _ in BEDROOM_CHOICES]

# модель → (queryset-функция, calculate-функция, requires_bedrooms)
MODELS: Mapping[str, tuple] = {
    "building": (
        lambda ids: Building.objects.exclude(dld_building__isnull=True).filter(
            pk__in=ids if ids else ()
        )
        if ids
        else Building.objects.exclude(dld_building__isnull=True),
        lambda obj, br: BuildingReport.calculate(obj, br),
        True,
    ),
    "area": (
        lambda ids: PF_Area.objects.filter(pk__in=ids)
        if ids
        else PF_Area.objects.all(),
        lambda obj, br: AreaReport.calculate(obj, br),
        True,
    ),
    "citypf": (
        lambda _ids: [None],  # один виртуальный объект
        lambda _dummy, br: CityReportPF.calculate(br),
        True,
    ),
    "citydld": (
        lambda _ids: [None],
        lambda _dummy, br: CityReport.calculate(br),
        True,
    ),
    "dldbuilding": (
        lambda ids: DldBuilding.objects.filter(pk__in=ids)
        if ids
        else DldBuilding.objects.all(),
        lambda obj, br: DldBuildingReport.calculate(obj, br),
        True,
    ),
    "areadld": (
        lambda ids: DLD_Area.objects.filter(pk__in=ids)
        if ids
        else DLD_Area.objects.all(),
        lambda obj, br: AreaReportDLD.calculate(obj, br),
        True,
    ),
}


class Command(BaseCommand):
    help = (
        "Гибкий пересчёт отчётов. Примеры:\n"
        "  python manage.py recalculate_reports --model building\n"
        "  python manage.py recalculate_reports --model building --id 42 --bedrooms 1br,2br\n"
        "  python manage.py recalculate_reports --model citypf --bedrooms studio\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            required=True,
            choices=MODELS.keys(),
            help="Тип отчёта: building | area | citypf | citydld | dldbuilding | areadld",
        )
        parser.add_argument(
            "--id",
            type=str,
            help="Один pk или список pk через запятую (для building/area/dldbuilding/areadld).",
        )
        parser.add_argument(
            "--bedrooms",
            type=str,
            help="Перечень типов спален через запятую "
            f"(допустимые: {', '.join(BR_CHOICES)}). По-умолчанию все.",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **opts):
        mkey: str = opts["model"]
        ids: Iterable[int] | None = (
            [int(x) for x in opts["id"].split(",")] if opts.get("id") else None
        )
        br_list: list[str] = (
            [x.strip() for x in opts["bedrooms"].split(",")]
            if opts.get("bedrooms")
            else BR_CHOICES
        )

        qs_fn, calc_fn, need_br = MODELS[mkey]

        # предварительные проверки
        unknown = [br for br in br_list if br not in BR_CHOICES]
        if unknown:
            self.stderr.write(
                self.style.ERROR(f"Неизвестные bedrooms: {', '.join(unknown)}")
            )
            return

        objects = list(qs_fn(ids))
        total = len(objects) * (len(br_list) if need_br else 1)
        self.stdout.write(f"Всего задач: {total}")

        processed = 0
        for obj in objects:
            targets = br_list if need_br else [None]
            for br in targets:
                try:
                    with transaction.atomic():
                        report = (
                            calc_fn(obj, br) if br is not None else calc_fn(obj, br)
                        )
                    status = (
                        self.style.SUCCESS("OK")
                        if report
                        else self.style.WARNING("SKIP")
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    status = self.style.ERROR(f"ERR ({exc})")
                name = f"{obj or '-'} / {br or '-'}"
                self.stdout.write(f"{status}: {name}")
                processed += 1
                self.stdout.write(f"Progress: {processed}/{total}", ending="\r")

        self.stdout.write(self.style.SUCCESS("✓ Всё готово"))

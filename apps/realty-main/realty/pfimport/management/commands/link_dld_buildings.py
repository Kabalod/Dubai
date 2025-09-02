# pfimport/management/commands/link_dld_buildings.py

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from rapidfuzz import process, fuzz

from realty.pfimport.models import Building as PfBuilding
from realty.main.models import Building as DldBuilding

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 75  # минимальный приемлемый score


class Command(BaseCommand):
    help = (
        "Для каждого pfimport.Building делает fuzzy‑match против всех "
        "DldBuilding.english_name и при max_score > DEFAULT_THRESHOLD "
        "сохраняет связь в поле dld_building."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            "-t",
            type=int,
            default=DEFAULT_THRESHOLD,
            help=f"Минимальный score для связывания (0–100), default={DEFAULT_THRESHOLD}",
        )
        parser.add_argument(
            "--limit",
            "-l",
            type=int,
            default=None,
            help="Обработать только первые N записей (для теста)",
        )

    def handle(self, *args, **options):
        thresh = options["threshold"]
        limit = options["limit"]

        # Загружаем кандидатов из DldBuilding
        dld_qs = DldBuilding.objects.filter(english_name__isnull=False).values_list(
            "id", "english_name"
        )
        choices = {name: pk for pk, name in dld_qs}

        self.stdout.write(f"Loaded {len(choices)} DldBuilding candidates")

        # Берём все PfBuilding без связи
        qs = PfBuilding.objects.filter(dld_building__isnull=True)
        if limit:
            qs = qs[:limit]
        total = qs.count()
        self.stdout.write(f"Processing {total} PfBuilding records...")

        for idx, pf in enumerate(qs, start=1):
            src_name = pf.name or ""
            # Найти лучший матч сразу среди всех english_name
            match = process.extractOne(
                src_name, choices.keys(), scorer=fuzz.token_sort_ratio
            )
            if not match:
                self.stdout.write(f"[{idx}/{total}] ✗ '{src_name}': нет кандидатов")
                continue

            best_name, score, _ = match
            if score <= thresh:
                self.stdout.write(
                    f"[{idx}/{total}] ✗ '{src_name}': лучший '{best_name}' score={score} ≤ threshold={thresh}"
                )
                continue

            # Сохраняем в БД
            dld_pk = choices[best_name]
            with transaction.atomic():
                pf.dld_building_id = dld_pk
                pf.save(update_fields=["dld_building"])

            self.stdout.write(
                f"[{idx}/{total}] ✓ '{src_name}' → '{best_name}' (score={score})"
            )

        self.stdout.write("Done.")

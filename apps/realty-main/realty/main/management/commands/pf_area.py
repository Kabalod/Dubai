# ─── import_geojson_areas.py ──────────────────────────────────────────────────
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rapidfuzz import fuzz, process
from shapely.geometry import shape, Point

from realty.pfimport.models import Area  # ← модель из pfimport
from realty.main.models import Building  # ← модель из main

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Импортирует *.geojson файлы в pfimport.Area и
    связывает main.Building с районом по координатам.
    """

    help = (
        "Импорт районов из GeoJSON и присвоение зданий.\n"
        "Пример:  python manage.py import_geojson_areas --dir data/geojsons --assign-buildings"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            required=True,
            type=str,
            help="Директория, где лежат *.geojson",
        )
        parser.add_argument(
            "--fuzzy-threshold",
            type=int,
            default=85,
            help="Минимальный RapidFuzz‑score для совпадения названия",
        )
        parser.add_argument(
            "--assign-buildings",
            action="store_true",
            help="Если передано — сразу проставит Building.area",
        )

    # ──────────────────────────────────────────────────────────────────────────
    @transaction.atomic
    def handle(self, *args, **opts):
        geo_dir = Path(opts["dir"]).expanduser().resolve()
        if not geo_dir.exists() or not geo_dir.is_dir():
            raise CommandError(f"Directory {geo_dir} not found.")

        fuzzy_th = opts["fuzzy_threshold"]
        assign = opts["assign_buildings"]

        self.stdout.write(f"Scanning {geo_dir} (threshold={fuzzy_th}) …")

        # Список текущих названий для фаззи‑поиска
        existing_names = list(Area.objects.values_list("name", flat=True))

        created, updated = 0, 0
        for geo_file in sorted(geo_dir.glob("*.geojson")):
            with open(geo_file, "r", encoding="utf‑8") as fh:
                data = json.load(fh)

            #             # Берём имя из Feature[0].properties (переопределите при иной структуре)
            #             first_feature = data["features"][0]
            #             area_name = (
            #                 first_feature.get("properties", {}).get("name")      # generic
            #                 or first_feature.get("properties", {}).get("name_en")  # your spec
            #             )
            #             if not area_name:
            #                 logger.warning(f"{geo_file} skipped – no 'name' in properties.")
            #                 continue
            #                 @@
            # -            first_feature = data["features"][0]
            # -            area_name = (
            # -                first_feature.get("properties", {}).get("name")
            # -                or first_feature.get("properties", {}).get("name_en")
            # -            )
            # -            if not area_name:
            # -                logger.warning(f"{geo_file} skipped – no 'name' in properties.")
            # -                continue
            # -
            # -            # Геометрия
            # -            geom_obj = shape(first_feature["geometry"])
            # -            geom_json = json.loads(json.dumps(first_feature["geometry"]))
            # --- берём ПЕРВУЮ фичу, где geometry != None --------------------
            feature_iter = (
                feat for feat in data.get("features", []) if feat.get("geometry")
            )
            first_feature = next(feature_iter, None)
            if not first_feature:
                logger.warning(f"{geo_file} skipped – no geometry found.")
                continue

            area_name = first_feature.get("properties", {}).get(
                "name"
            ) or first_feature.get("properties", {}).get("name_en")
            if not area_name:
                # fallback: имя файла без расширения
                area_name = geo_file.stem.replace("_", " ").title()

            # Геометрия
            try:
                geom_obj = shape(first_feature["geometry"])
            except Exception as exc:
                logger.warning(f"{geo_file} skipped – invalid geometry ({exc}).")
                continue
            geom_json = first_feature["geometry"]  # уже dict

            #
            # # Геометрия
            # geom_obj = shape(first_feature["geometry"])
            # geom_json = json.loads(json.dumps(first_feature["geometry"]))

            # Ищем совпадение
            match_name, score = (None, 0)
            #             if existing_names:
            #                 match_name, score = process.extractOne(
            #                     area_name, existing_names, scorer=fuzz.token_sort_ratio
            #                 )
            #                 @@
            # -            if existing_names:
            # -                match_name, score = process.extractOne(
            # -                    area_name, existing_names, scorer=fuzz.token_sort_ratio
            # -                )
            if existing_names:
                # extractOne → (best_match, score, idx). Индекс не нужен.
                result = process.extractOne(
                    area_name, existing_names, scorer=fuzz.token_sort_ratio
                )
                if result:
                    match_name, score, _ = result
                else:
                    match_name, score = None, 0

            if score >= fuzzy_th:
                # Update существующей записи (дописываем геометрию при необходимости)
                area_obj = Area.objects.get(name=match_name)
                if not area_obj.geometry_json:
                    area_obj.geometry_json = geom_json
                    area_obj.save(update_fields=["geometry_json"])
                updated += 1
                logger.info(f"Matched '{area_name}' → '{match_name}' ({score})")
            else:
                # Создаём новую
                area_obj = Area.objects.create(
                    name=area_name,
                    numeric_area=geom_obj.area,
                    geometry_json=geom_json,
                    created_by="geojson_import",
                )
                existing_names.append(area_name)  # для следующих файлов
                created += 1
                logger.info(f"Created new area '{area_name}'")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import complete: created={created}, updated={updated}"
            )
        )

        # ───── Optional: проставляем Building.area ─────
        if assign:
            self.stdout.write("Assigning buildings to areas …")
            assigned, skipped = 0, 0
            # Готовим in‑memory список (area_obj, shapely_polygon)
            area_polygons = [
                (a, shape(a.geometry_json))
                for a in Area.objects.exclude(geometry_json=None)
            ]

            for b in Building.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
            ):
                pt = Point(b.longitude, b.latitude)
                target_area = None
                for area_obj, poly in area_polygons:
                    if poly.contains(pt):
                        target_area = area_obj
                        break

                if target_area:
                    if b.area_id != target_area.pk:
                        b.area_by_pf = target_area
                        b.save(update_fields=["area_by_pf"])
                    assigned += 1
                else:
                    skipped += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Buildings assigned: {assigned}, skipped: {skipped}"
                )
            )

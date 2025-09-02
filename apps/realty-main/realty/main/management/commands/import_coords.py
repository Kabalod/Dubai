import os
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from realty.main.models import Project, Location, Building, Land


class Command(BaseCommand):
    help = (
        "Импортирует из JSON-ов координаты:\n"
        " • в модель Location (OneToOne с Project)\n"
        " • в связанные Building и Land (для существующих записей),\n"
        "   а также задаёт координаты для Building из project.location, если явно не указаны\n"
        "Аргумент: путь к корню директории с JSON-файлами."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "json_dir", type=str, help="Путь к директории, содержащей JSON-файлы"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        root_dir = options["json_dir"]
        if not os.path.isdir(root_dir):
            self.stderr.write(self.style.ERROR(f"Папка не найдена: {root_dir}"))
            return

        total = {"projects": 0, "buildings": 0, "lands": 0, "defaults": 0}

        for dirpath, _, files in os.walk(root_dir):
            for fname in files:
                if not fname.lower().endswith(".json"):
                    continue

                full_path = os.path.join(dirpath, fname)
                try:
                    payload = json.load(open(full_path, encoding="utf-8"))
                except Exception as e:
                    self.stderr.write(f"Не прочитался {full_path}: {e}")
                    continue

                resp = payload.get("response", {})
                proj_data = resp.get("project")
                if not proj_data:
                    continue

                # Найдём первый Project по номеру
                proj_num = proj_data.get("title", {}).get("number")
                if not proj_num:
                    continue
                qs_proj = Project.objects.filter(project_number=proj_num)
                if not qs_proj.exists():
                    self.stderr.write(
                        f"Project {proj_num} не найден в БД, файл {fname}"
                    )
                    continue
                if qs_proj.count() > 1:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Найдено {qs_proj.count()} проектов с project_number={proj_num}, используем первый."
                        )
                    )
                project = qs_proj.first()

                # 1) Location
                coords = proj_data.get("location", {}).get("googleCoordinates", {})
                lat = coords.get("latitude")
                lng = coords.get("longitude")
                if lat is not None and lng is not None:
                    Location.objects.update_or_create(
                        project=project, defaults={"latitude": lat, "longitude": lng}
                    )
                    total["projects"] += 1

                # 2) Buildings из JSON
                for b in proj_data.get("buidlings", []):
                    loc = b.get("location", {})
                    blat, blng = loc.get("latitude"), loc.get("longitude")
                    if blat is None or blng is None:
                        continue
                    eng = b.get("name", {}).get("englishName")
                    qs_b = Building.objects.filter(project=project)
                    if eng:
                        qs_b = qs_b.filter(english_name=eng)
                    else:
                        num = b.get("number")
                        qs_b = qs_b.filter(number=num) if num else qs_b.none()
                    updated = qs_b.update(latitude=blat, longitude=blng)
                    total["buildings"] += updated

                # 3) Lands из JSON
                for l in proj_data.get("lands", []):
                    loc = l.get("location", {})
                    llat, llng = loc.get("latitude"), loc.get("longitude")
                    if llat is None or llng is None:
                        continue
                    eng_l = l.get("name", {}).get("englishName")
                    qs_l = Land.objects.filter(project=project)
                    if eng_l:
                        qs_l = qs_l.filter(english_name=eng_l)
                    else:
                        num_l = l.get("number")
                        qs_l = qs_l.filter(number=num_l) if num_l else qs_l.none()
                    updated = qs_l.update(latitude=llat, longitude=llng)
                    total["lands"] += updated

        # 4) Defaults для Building без coords: берем из project.location
        buildings_no = Building.objects.filter(
            latitude__isnull=True, longitude__isnull=True
        )
        for b in buildings_no.select_related("project__location"):
            loc = getattr(b.project, "location", None)
            if loc and loc.latitude is not None and loc.longitude is not None:
                b.latitude = loc.latitude
                b.longitude = loc.longitude
                b.save(update_fields=["latitude", "longitude"])
                total["defaults"] += 1

        # Итоги
        self.stdout.write(
            self.style.SUCCESS(f"Projects (Location) updated: {total['projects']}")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Buildings coords updated from JSON: {total['buildings']}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f"Lands coords updated from JSON: {total['lands']}")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Buildings coords defaulted from project: {total['defaults']}"
            )
        )

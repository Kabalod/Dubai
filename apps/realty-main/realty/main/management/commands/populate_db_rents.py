import csv
import datetime
import gc
import re
from decimal import Decimal
from decimal import InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from rapidfuzz import fuzz
from rapidfuzz import process
from realty.main.models import Area
from realty.main.models import Building
from realty.main.models import MergedRentalTransaction
from realty.main.models import Project


class Command(BaseCommand):
    help = "Fill MergedRentalTransaction from a large CSV file (in chunks)."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file", type=str, help="Path to the CSV file with rental data."
        )

        parser.add_argument(
            "--clean-first",
            action="store_true",
            help="Перед началом удалить все записи MergedRentalTransaction без подтверждения.",
        )
        parser.add_argument(
            "--start-line",
            type=int,
            default=1,
            help="Номер строки (1-based), с которой начинать обработку CSV (включая заголовок).",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        start_line = options.get("start_line", 1)
        # посчитаем общее число строк (включая заголовок)
        total_lines = sum(1 for _ in Path(csv_file).open(mode="r", encoding="utf-8"))
        self.stdout.write(
            self.style.NOTICE(f"Начинаю обработку с строки {start_line}/{total_lines}")
        )

        # 1) Спросим у пользователя, нужно ли очистить данные:
        # confirm = input(
        #     "Очистить все записи в MergedRentalTransaction перед началом? (y/n): "
        # )
        # if confirm.lower().startswith("y"):
        # 1) Очистить данные?
        if options["clean_first"]:
            self.stdout.write(self.style.WARNING("Чищу MergedRentalTransaction…"))
            MergedRentalTransaction.objects.all().delete()
            self.stdout.write(
                self.style.WARNING("Все записи MergedRentalTransaction удалены.")
            )
        elif sys.stdin.isatty():  # есть TTY → спрашиваем
            confirm = input(
                "Очистить все записи в MergedRentalTransaction перед началом? (y/n): "
            )
            if confirm.lower().startswith("y"):
                MergedRentalTransaction.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING("Все записи MergedRentalTransaction удалены.")
                )

        file_path = Path(csv_file)
        if not file_path.exists():
            raise CommandError(f"Файл {csv_file} не существует.")

        # Составим справочники Projects, Areas и Buildings один раз, чтобы быстрее делать fuzzy-поиск.
        self.init_cached_data()

        # self.process_file_in_chunks(file_path)
        # передаём start_line и total_lines
        self.process_file_in_chunks(
            file_path, chunk_size=5000, start_line=start_line, total_lines=total_lines
        )
        self.stdout.write(
            self.style.SUCCESS(f"Всего строк во входном файле: {total_lines}")
        )

    def init_cached_data(self):
        """
        Считываем один раз все Project, Area и Building,
        чтобы потом быстро искать по fuzzy и определять building для проекта.
        """
        self.all_projects = list(Project.objects.all().values("id", "english_name"))
        self.all_areas = list(Area.objects.all().values("id", "name_en"))

        buildings_qs = Building.objects.all().values(
            "id", "project_id", "english_name", "building_count"
        )
        self.buildings_by_project_id = {}
        for b in buildings_qs:
            pid = b["project_id"]
            self.buildings_by_project_id.setdefault(pid, [])
            self.buildings_by_project_id[pid].append(
                (b["id"], b["english_name"], b["building_count"])
            )

        self.project_names = []
        for pr in self.all_projects:
            if pr["english_name"]:
                self.project_names.append(pr["english_name"])

        self.area_names = []
        for ar in self.all_areas:
            if ar["name_en"]:
                self.area_names.append(ar["name_en"])

    # def process_file_in_chunks(self, file_path: Path, chunk_size=5000):
    def process_file_in_chunks(
        self, file_path: Path, chunk_size=5000, start_line=1, total_lines=None
    ):
        """
        Читаем CSV по 5000 строк, обрабатываем, вызываем GC, повторяем.
        """
        with file_path.open(mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            rows_buffer = []
            # for row in reader:
            # enumerate начиная с 2, т.к. header – строка 1
            for idx, row in enumerate(reader, start=2):
                # пропускаем до нужной стартовой
                if idx < start_line:
                    continue

                rows_buffer.append(row)
                # if len(rows_buffer) >= chunk_size:
                if len(rows_buffer) >= chunk_size:
                    # выводим прогресс
                    self.stdout.write(
                        self.style.NOTICE(f"Обрабатываю строку {idx}/{total_lines}")
                    )

                    self.handle_chunk(rows_buffer)
                    rows_buffer.clear()
                    gc.collect()

            # Остаток
            if rows_buffer:
                self.stdout.write(
                    self.style.NOTICE(f"Обрабатываю строку {idx}/{total_lines}")
                )

                rows_buffer.clear()
                gc.collect()

    @transaction.atomic
    def handle_chunk(self, rows):
        for row in rows:
            if not self.row_is_relevant(row):
                continue

            # 1. Найдём / создадим Area:
            area_obj = self.find_or_create_area(row)

            # 2. Найдём / создадим Project:
            project_obj = self.find_or_create_project(row)

            # 3. Найдём Building (если project_obj не None)
            building_obj = self.find_building(project_obj)

            # 4. Создадим / обновим MergedRentalTransaction
            self.create_or_update_merged_rental(
                row, area_obj, project_obj, building_obj
            )

    def row_is_relevant(self, row) -> bool:
        """
        - ejari_bus_property_type_en == "Unit"
        - ejari_property_type_en == "Flat"
        - заполнено (project_name_en или master_project_en).
        """
        if row.get("ejari_bus_property_type_en") != "Unit":
            return False
        if row.get("ejari_property_type_en") != "Flat":
            return False

        p_en = (row.get("project_name_en") or "").strip()
        mp_en = (row.get("master_project_en") or "").strip()

        if not p_en and not mp_en:
            return False

        return True

    def find_or_create_area(self, row):
        """
        Fuzzy-поиск по area_name_en.
        Если нет, создаём новую Area.
        """
        area_name_en = (row.get("area_name_en") or "").strip()
        if not area_name_en:
            return None

        match = process.extractOne(area_name_en, self.area_names, scorer=fuzz.WRatio)
        if match and match[1] > 80:
            matched_str = match[0]
            for a in self.all_areas:
                if a["name_en"] == matched_str:
                    return Area.objects.get(id=a["id"])

        new_area = Area.objects.create(
            area_idx=self.safe_int(row.get("area_id")),
            name_ar=row.get("area_name_ar") or None,
            name_en=area_name_en,
        )
        self.all_areas.append({"id": new_area.id, "name_en": new_area.name_en})
        self.area_names.append(new_area.name_en)
        return new_area

    def find_or_create_project(self, row):
        """
        1) Если есть project_name_en -> fuzzy-поиск;
           если не нашли, тогда пытаемся master_project_en;
           если не нашли, создаём.
        """
        p_en = (row.get("project_name_en") or "").strip()
        mp_en = (row.get("master_project_en") or "").strip()

        # arabic_name возьмём из master_project_ar или project_name_ar.
        arabic_name_from_csv = (row.get("master_project_ar") or "").strip()
        if not arabic_name_from_csv and row.get("project_name_ar"):
            arabic_name_from_csv = row.get("project_name_ar")

        candidates = []
        if p_en:
            candidates.append(p_en)
        if mp_en:
            candidates.append(mp_en)

        for candidate_name in candidates:
            project_obj = self.find_project_by_fuzzy(candidate_name)
            if project_obj:
                return project_obj

        final_english = p_en if p_en else mp_en
        project_number = row.get("project_number") or ""
        new_proj = Project.objects.create(
            project_number=project_number,
            english_name=final_english,
            arabic_name=arabic_name_from_csv,
        )
        self.all_projects.append(
            {"id": new_proj.id, "english_name": new_proj.english_name}
        )
        if new_proj.english_name and new_proj.english_name not in self.project_names:
            self.project_names.append(new_proj.english_name)

        return new_proj

    def find_project_by_fuzzy(self, candidate_name):
        match = process.extractOne(
            candidate_name, self.project_names, scorer=fuzz.WRatio
        )
        if match and match[1] > 80:
            matched_str = match[0]
            for pr in self.all_projects:
                if pr["english_name"] == matched_str:
                    return Project.objects.get(id=pr["id"])
        return None

    def find_building(self, project_obj):
        if not project_obj:
            return None
        pid = project_obj.id
        if pid not in self.buildings_by_project_id:
            return None

        candidates = self.buildings_by_project_id[pid]
        # building_count == 1
        candidates = [c for c in candidates if c[2] == 1]

        if len(candidates) == 1:
            building_id, eng_name, bcount = candidates[0]
            return Building.objects.get(id=building_id)
        return None

    def create_or_update_merged_rental(self, row, area_obj, project_obj, building_obj):
        """
        Создаём/обновляем MergedRentalTransaction по (contract_id, date_of_transaction),
        и заполняем:
          - transaction_price = Decimal(contract_amount)
          - sqm = actual_area
          - location_name = area_name_en
          - meter_sale_price = transaction_price / Decimal(str(sqm)) (если sqm>0)
          - period = вычисляем по разнице между today и date_of_transaction
          - number_of_rooms = "2 B/R" (преобразование через convert_rooms_string)
        """
        contract_id = (row.get("contract_id") or "").strip()
        start_date = self.parse_date(row.get("contract_start_date"))
        date_of_transaction = start_date if start_date else timezone.now().date()

        # Считаем transaction_price (Decimal)
        transaction_price = self.safe_decimal(row.get("contract_amount"))

        # Считаем sqm (float)
        sqm = self.safe_float(row.get("actual_area"))

        # Логика meter_sale_price
        if transaction_price and sqm and sqm > 0:
            meter_sale_price = transaction_price / Decimal(str(sqm))
        else:
            meter_sale_price = None

        # location_name = area_name_en
        location_name = (row.get("area_name_en") or "").strip()

        # number_of_rooms (из ejari_property_sub_type_en)
        raw_rooms_str = (row.get("ejari_property_sub_type_en") or "").lower()
        number_of_rooms = self.convert_rooms_string(raw_rooms_str)

        # period
        period_value = self.get_period(date_of_transaction)

        defaults = {
            "transaction_type": "rental",
            "building": building_obj,
            "project": project_obj,
            "area": area_obj,
            "date_of_transaction": date_of_transaction,
            "building_name": building_obj.english_name if building_obj else None,
            "location_name": location_name,
            "number_of_rooms": number_of_rooms,
            "sqm": sqm,
            "transaction_price": transaction_price,
            "meter_sale_price": meter_sale_price,
            "detail_link": None,  # Если нужно заполнять - возьмите из CSV
            "contract_start_date": start_date,
            "contract_end_date": self.parse_date(row.get("contract_end_date")),
            "contract_reg_type_id": row.get("contract_reg_type_id") or None,
            "contract_reg_type_ar": row.get("contract_reg_type_ar") or None,
            "contract_reg_type_en": row.get("contract_reg_type_en") or None,
            "annual_amount": self.safe_float(row.get("annual_amount")),
            "no_of_prop": self.safe_int(row.get("no_of_prop")),
            "line_number": self.safe_int(row.get("line_number")),
            "is_free_hold": True if (row.get("is_free_hold") == "1") else False,
            "ejari_bus_property_type_id": row.get("ejari_bus_property_type_id"),
            "ejari_bus_property_type_ar": row.get("ejari_bus_property_type_ar"),
            "ejari_bus_property_type_en": row.get("ejari_bus_property_type_en"),
            "ejari_property_type_id": row.get("ejari_property_type_id"),
            "ejari_property_type_en": row.get("ejari_property_type_en"),
            "ejari_property_type_ar": row.get("ejari_property_type_ar"),
            "ejari_property_sub_type_id": row.get("ejari_property_sub_type_id"),
            "ejari_property_sub_type_en": row.get("ejari_property_sub_type_en"),
            "ejari_property_sub_type_ar": row.get("ejari_property_sub_type_ar"),
            "property_usage_en": row.get("property_usage_en"),
            "property_usage_ar": row.get("property_usage_ar"),
            "project_number": row.get("project_number"),
            "project_name_ar": row.get("project_name_ar"),
            "project_name_en": row.get("project_name_en"),
            "master_project_ar": row.get("master_project_ar"),
            "master_project_en": row.get("master_project_en"),
            "area_id_csv": self.safe_int(row.get("area_id")),
            "area_name_ar": row.get("area_name_ar"),
            "area_name_en": row.get("area_name_en"),
            "actual_area": sqm,
            "nearest_landmark_ar": row.get("nearest_landmark_ar"),
            "nearest_landmark_en": row.get("nearest_landmark_en"),
            "nearest_metro_ar": row.get("nearest_metro_ar"),
            "nearest_metro_en": row.get("nearest_metro_en"),
            "nearest_mall_ar": row.get("nearest_mall_ar"),
            "nearest_mall_en": row.get("nearest_mall_en"),
            "tenant_type_id": self.safe_int(row.get("tenant_type_id")),
            "tenant_type_ar": row.get("tenant_type_ar"),
            "tenant_type_en": row.get("tenant_type_en"),
            "period": period_value,
        }

        if contract_id:
            # update_or_create по (contract_id, date_of_transaction)
            obj, created = MergedRentalTransaction.objects.update_or_create(
                contract_id=contract_id,
                date_of_transaction=date_of_transaction,
                defaults=defaults,
            )
        else:
            obj = MergedRentalTransaction.objects.create(**defaults)

    def convert_rooms_string(self, raw_string: str):
        """
        Преобразуем "2 bed rooms+hall" => "2 B/R", и т.п.
        При необходимости расширяйте логику/рег.выражения.
        """
        pattern = r"(\d+)\s*bed\s*room(s)?\+hall"
        replaced = re.sub(pattern, r"\1 B/R", raw_string, flags=re.IGNORECASE).strip()

        # Если не удалось, пробуем ещё один вариант с пробелами между +:
        if replaced == raw_string:
            pattern2 = r"(\d+)\s*bed\s*room(s?)\s*\+\s*hall"
            replaced2 = re.sub(
                pattern2, r"\1 B/R", replaced, flags=re.IGNORECASE
            ).strip()
            if replaced2 != replaced:
                replaced = replaced2

        if not replaced:
            replaced = None

        return replaced

    def get_period(self, date_of_transaction):
        """
        Возвращаем "1 week", "1 month", "3 month", "6 month", "1 year", "2 years",
        либо "older than 2 years" в зависимости от diff.days
        """
        if not date_of_transaction:
            return None
        today = datetime.date.today()
        diff_days = (today - date_of_transaction).days

        if diff_days <= 7:
            return "1 week"
        elif diff_days <= 30:
            return "1 month"
        elif diff_days <= 90:
            return "3 month"
        elif diff_days <= 180:
            return "6 month"
        elif diff_days <= 365:
            return "1 year"
        elif diff_days <= 730:
            return "2 years"
        else:
            return "older than 2 years"

    def parse_date(self, date_str):
        if not date_str:
            return None
        date_str = date_str.strip()
        parts = date_str.split("-")
        if len(parts) == 3:
            dd, mm, yyyy = parts
            try:
                return timezone.datetime(
                    year=int(yyyy), month=int(mm), day=int(dd)
                ).date()
            except ValueError:
                return None
        return None

    def safe_int(self, val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    def safe_float(self, val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    def safe_decimal(self, val):
        if not val:
            return None
        try:
            return Decimal(val)
        except (InvalidOperation, TypeError):
            return None

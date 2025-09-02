import csv
import datetime
import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from realty.main.models import Area
from realty.main.models import Building
from realty.main.models import BuildingLiquidityParameterOne
from realty.main.models import MergedTransaction
from realty.main.models import Project


class Command(BaseCommand):
    """
    Пример вызова:
        python manage.py populate_db \
            --giper_csv="/full/path/to/giper_matched_output.csv" \
            --transactions_csv="/full/path/to/tr_28_03_2025.csv" \
            --chunk-size=5000

    По умолчанию (без аргументов) возьмёт файлы giper_matched_output.csv и tr_28_03_2025.csv
    из текущей директории, chunk_size=5000.
    """

    help = "Populates the DB with buildings and transactions, clearing all old data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--giper_csv",
            type=str,
            default="giper_matched_output.csv",
            help="Путь к файлу giper_matched_output.csv",
        )
        parser.add_argument(
            "--transactions_csv",
            type=str,
            default="tr_28_03_2025.csv",
            help="Путь к файлу tr_28_03_2025.csv (очень большой)",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=5000,
            help="Размер порции (bulk_create) для транзакций",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        giper_csv_path = options["giper_csv"]
        transactions_csv_path = options["transactions_csv"]
        chunk_size = options["chunk_size"]

        # 1) Сносим всё из связанных таблиц
        self._clean_all()

        # 2) Загружаем данные из giper_matched_output.csv
        if not os.path.isfile(giper_csv_path):
            raise CommandError(f"Файл {giper_csv_path} не найден.")
        self.stdout.write(self.style.SUCCESS(f"Loading from {giper_csv_path}..."))
        self._load_giper_data(giper_csv_path)

        # 3) Загружаем транзакции из tr_28_03_2025.csv
        if not os.path.isfile(transactions_csv_path):
            raise CommandError(f"Файл {transactions_csv_path} не найден.")
        self.stdout.write(
            self.style.SUCCESS(f"Loading from {transactions_csv_path}...")
        )
        self._load_transactions_in_chunks(transactions_csv_path, chunk_size)

        self.stdout.write(self.style.SUCCESS("Done populating DB!"))

    def _clean_all(self):
        self.stdout.write(self.style.WARNING("Deleting old data..."))
        MergedTransaction.objects.all().delete()
        BuildingLiquidityParameterOne.objects.all().delete()
        Building.objects.all().delete()
        Project.objects.all().delete()
        Area.objects.all().delete()
        self.stdout.write(self.style.WARNING("All old data removed."))

    def _load_giper_data(self, csv_path):
        """
        Считывает giper_matched_output.csv и создаёт:
          Area, Project, Building.
        Если нет project_name_en_out и project_number => building привязывается к проекту "unknow project".
        Кроме того, для Building записываем (в facilities, например) словари вида {
          "1 B/R": int(...),
          "2 B/R": ...,
          ...
        } для подсчёта same_rooms_count_in_building.
        """
        self.unknown_project = Project.objects.create(english_name="unknow project")

        area_map = {}
        project_map = {}
        building_map = {}

        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 1) создаём/находим Area
                area_name_en = (row.get("area_name_en_out") or "").strip()
                if area_name_en:
                    if area_name_en not in area_map:
                        area_obj = Area.objects.create(name_en=area_name_en)
                        area_map[area_name_en] = area_obj
                    else:
                        area_obj = area_map[area_name_en]
                else:
                    # Если пусто, можно оставить area=None (или создать "Unknown area"?)
                    area_obj = None

                # 2) создаём/находим Project
                project_name_en = (row.get("project_name_en_out") or "").strip()
                project_number = (row.get("project_number") or "").strip()
                total_units_str = row.get("total_units") or ""
                try:
                    total_units = int(total_units_str) if total_units_str else None
                except ValueError:
                    total_units = None

                # Ключ для project_map – например, (project_name_en, project_number, area_name_en)
                # В зависимости от того, насколько уникальны ваши данные.
                # Или просто project_number, если он уникален.
                if project_name_en or project_number:
                    project_key = (project_name_en, project_number, area_name_en)
                    if project_key not in project_map:
                        # создаём новый
                        proj = Project.objects.create(
                            english_name=project_name_en if project_name_en else None,
                            project_number=project_number if project_number else None,
                            total_units=total_units,
                            # Можем привязать Project к area, если по ТЗ нужно (не всегда это требуется)
                            # В моделях нет прямого FK Project->Area, но если нужно - добавьте поле
                            # ИЛИ же можно просто игнорировать area тут.
                        )
                        project_map[project_key] = proj
                    else:
                        proj = project_map[project_key]
                else:
                    # Нет project_name, значит привязываем к unknown_project
                    proj = self.unknown_project

                # 3) создаём Building
                building_name_en = (row.get("building_name_en_out") or "").strip()
                if not building_name_en:
                    # Если и у здания пустое имя - можно пропустить или дать "Unnamed"
                    continue

                floor_count_str = row.get("этажей") or ""
                try:
                    floor_count = int(floor_count_str)
                except ValueError:
                    floor_count = None

                building_count_str = row.get("Количество билдингов в проекте") or ""
                try:
                    building_count_val = int(building_count_str)
                except ValueError:
                    building_count_val = None

                # Собираем данные о комнатах
                # У giper_matched_output.csv есть столбцы "1br","2br","3br","4br","other"
                # Для удобства положим в словарь building_facilities["rooms_count"] = {...}
                building_facilities = {}
                building_facilities["rooms_count"] = {
                    "1 B/R": self._safe_int(row.get("1br")),
                    "2 B/R": self._safe_int(row.get("2br")),
                    "3 B/R": self._safe_int(row.get("3br")),
                    "4 B/R": self._safe_int(row.get("4br")),
                    "other": self._safe_int(row.get("other")),
                }

                # total_units
                b_total_units_str = row.get("total_units") or ""
                try:
                    b_total_units = int(b_total_units_str)
                except ValueError:
                    b_total_units = None

                # Создадим Building
                b = Building.objects.create(
                    project=proj,
                    area=area_obj,
                    english_name=building_name_en,
                    floor_count=floor_count,
                    building_count=building_count_val,
                    total_units=b_total_units,
                )
                # Сохраним словарь в building.facilities (или another JSONField)
                # Но у модели Building в исходном коде нет JSONField,
                # можно хранить в building.property_type или building.arabic_name,
                # но лучше расширить модель.
                # Для примера допустим, что "arabic_name" для нас свободно или
                # используем "property_type" как JSON. Это не очень корректно, но покажем идею:
                b.property_type = "RoomsData"  # какая-то пометка
                # а сами counts в extra поле "facilities"?
                # Но нет "facilities" в модели. Пришлось бы добавить поле.
                # Чтобы уместиться в ТЗ – покажем вариант хранения словаря в python:
                # создадим поле "facilities" если вы можете. Если нет – вариантов два:
                #   A) Расширить модель
                #   B) Хранить как текст JSON
                # Предположим, что "arabic_name" нам не нужно, и туда упрячем JSON
                import json

                b.arabic_name = json.dumps(building_facilities)
                b.save()

                # Сохраним в building_map, чтобы потом легче искать по building_name_en
                building_map[building_name_en.lower()] = b

        # Сохраняем полученные словари как атрибуты self,
        # чтобы далее переиспользовать в транзакциях
        self.area_map = area_map
        self.project_map = project_map
        self.building_map = building_map

    def _load_transactions_in_chunks(self, csv_path, chunk_size):
        """
        Из файла tr_28_03_2025.csv (огромного) построчно читаем, создаём MergedTransaction.
        transaction_type = 'sales'.
        Вычисляем:
            building_rooms_count (если у проекта 1 здание => project.total_units, иначе 0),
            same_rooms_count_in_building (по rooms_en + building.facilities["rooms_count"]).
        По итогу считаем LiquidityParameterOne -> количество сделок (sales) в (год,месяц) для каждого Building.
        """
        transactions_buffer = []
        self.liquidity_counter = {}  # (building_id, year, month) -> count

        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            row_count = 0

            for row in reader:
                row_count += 1

                # 1) Основные поля
                transaction_type = "sales"  # по условию
                instance_date_str = row.get("instance_date") or ""
                try:
                    date_of_transaction = datetime.datetime.strptime(
                        instance_date_str, "%d-%m-%Y"
                    ).date()
                except ValueError:
                    # Непарсибельная дата - пропустим
                    continue

                # float/decimal поля
                procedure_area = self._safe_float(row.get("procedure_area"))
                actual_worth = self._safe_float(row.get("actual_worth"))
                meter_sale_price = self._safe_float(row.get("meter_sale_price"))

                # Поиск Building
                building_name_en = (row.get("building_name_en") or "").strip()
                bkey = building_name_en.lower()
                building_obj = self.building_map.get(bkey)  # или None

                # Поиск проекта (по project_name_en)
                project_name_en = (row.get("project_name_en") or "").strip()
                # Т.к. в _load_giper_data мы делали ключ (pn, pnum, area_name)
                # тут точно воспроизвести сложнее.
                # Либо вы там создаёте map по одному названию,
                # либо тоже "unknown project", если не найдено.
                # Упростим: попытаемся найти любой Project,
                # у которого english_name=project_name_en (lower).
                # Для быстрого поиска – сделаем словарь
                proj = None
                if project_name_en:
                    # итерируем по self.project_map, ищем подходящий
                    found = False
                    for (pname, pnum, aname), pobj in self.project_map.items():
                        if pname.lower() == project_name_en.lower():
                            proj = pobj
                            found = True
                            break
                    if not found:
                        # не нашли - unknown
                        proj = self.unknown_project
                else:
                    proj = self.unknown_project

                # Поиск area (по area_name_en)
                area_name_en = (row.get("area_name_en") or "").strip()
                area_obj = self.area_map.get(area_name_en)

                # building_rooms_count:
                #   = project.total_units, если у проекта ровно 1 здание, иначе 0.
                building_rooms_count = 0
                if proj and proj.total_units:
                    # Проверим, не кэшировали ли мы "сколько зданий"?
                    # Можно в конце _load_giper_data посчитать project->count(buildings).
                    # Но проще: project.buildings.count() -> может быть затратно, но приемлемо, если проектов мало.
                    # Для оптимизации – заранее посчитаем, как ниже.
                    if not hasattr(proj, "_buildings_count"):
                        proj._buildings_count = proj.buildings.count()
                    if proj._buildings_count == 1:
                        building_rooms_count = proj.total_units or 0

                # same_rooms_count_in_building:
                #   нужно извлечь rooms_en, а потом посмотреть, сколько в building.facilities["rooms_count"].
                #   "rooms_en" может быть "1 B/R","2 B/R","3 B/R","4 B/R","Studio" и т.д.
                rooms_en = (row.get("rooms_en") or "").strip()
                same_rooms_count = 0
                if building_obj and building_obj.arabic_name:
                    # Распарсим json
                    import json

                    try:
                        b_fac = json.loads(building_obj.arabic_name)
                        room_map = b_fac.get("rooms_count", {})
                        # Сопоставляем "1 B/R" -> room_map["1 B/R"]
                        # Можно сделать простейший if:
                        if rooms_en in room_map:
                            same_rooms_count = room_map[rooms_en]
                        else:
                            same_rooms_count = room_map.get("other", 0)
                    except:
                        pass

                # Год сделки
                deal_year = date_of_transaction.year
                deal_month = date_of_transaction.month

                # В liquidity_counter прибавим 1
                if building_obj:
                    key = (building_obj.id, deal_year, deal_month)
                    self.liquidity_counter[key] = self.liquidity_counter.get(key, 0) + 1

                # Собираем объект для MergedTransaction
                mt = MergedTransaction(
                    transaction_type=transaction_type,
                    building=building_obj,
                    date_of_transaction=date_of_transaction,
                    building_name=building_name_en,
                    location_name=area_name_en,
                    number_of_rooms=rooms_en,
                    sqm=procedure_area,
                    transaction_price=actual_worth,
                    meter_sale_price=meter_sale_price,
                    deal_year=deal_year,
                    area=area_obj,
                    building_rooms_count=building_rooms_count,
                    same_rooms_count_in_building=same_rooms_count,
                )
                transactions_buffer.append(mt)

                # bulk_create порциями
                if len(transactions_buffer) >= chunk_size:
                    MergedTransaction.objects.bulk_create(transactions_buffer)
                    self.stdout.write(f"  Imported {row_count} rows so far...")
                    transactions_buffer.clear()

            # Финальный кусок
            if transactions_buffer:
                MergedTransaction.objects.bulk_create(transactions_buffer)
                self.stdout.write(f"  Finished importing {row_count} rows total.")

        # Теперь сохраним BuildingLiquidityParameterOne
        self.stdout.write("Filling BuildingLiquidityParameterOne ...")
        blpo_bulk = []
        for (building_id, year, month), cnt in self.liquidity_counter.items():
            blpo_bulk.append(
                BuildingLiquidityParameterOne(
                    building_id=building_id,
                    year=year,
                    month=month,
                    liquidity_parameter_one=cnt,
                )
            )
        BuildingLiquidityParameterOne.objects.bulk_create(blpo_bulk)
        self.stdout.write(
            f"Done BuildingLiquidityParameterOne: {len(blpo_bulk)} records."
        )

    def _safe_float(self, val):
        """Возвращает float(val) или 0.0, если не парсится."""
        if not val:
            return 0.0
        try:
            return float(val)
        except ValueError:
            return 0.0

    def _safe_int(self, val):
        """Возвращает int(val) или 0, если не парсится."""
        if not val:
            return 0
        try:
            return int(val)
        except ValueError:
            return 0

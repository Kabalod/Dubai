# realty/main/management/commands/la.py
import pandas as pd
from django.core.management.base import BaseCommand
from realty.main.models import MasterProject, Project, MergedRentalTransaction


class Command(BaseCommand):
    help = "Импорт master-проектов из Excel и связывание с проектами и транзакциями"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", "-f", required=True, help="Путь до Excel-файла с данными"
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        self.stdout.write(f"Чтение файла {file_path}…")
        df = pd.read_excel(file_path)

        cols = set(df.columns.tolist())
        self.stdout.write(f"Найдены колонки: {', '.join(sorted(cols))}")
        needed = {
            "project_name_en_out",
            "master_project_en_out",
            "master_project_ar_out",
            "transaction_id",
        }
        missing = needed - cols
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"В файле нет колонок: {', '.join(missing)} — они будут проигнорированы."
                )
            )

        # --- 1) Создаём MasterProject ---
        # берем только english, а арабское имя — если есть
        mp_subset = ["master_project_en_out"]
        if "master_project_ar_out" in cols:
            mp_subset.append("master_project_ar_out")

        mp_df = (
            df[mp_subset]
            .drop_duplicates(subset=["master_project_en_out"])
            .dropna(subset=["master_project_en_out"])
        )
        for _, row in mp_df.iterrows():
            name_en = str(row["master_project_en_out"]).strip()
            name_ar = (
                str(row["master_project_ar_out"]).strip()
                if "master_project_ar_out" in cols
                and pd.notna(row.get("master_project_ar_out"))
                else None
            )
            mp, created = MasterProject.objects.get_or_create(
                english_name=name_en, defaults={"arabic_name": name_ar}
            )
            if not created and name_ar and mp.arabic_name != name_ar:
                mp.arabic_name = name_ar
                mp.save()

        mp_map = {mp.english_name: mp for mp in MasterProject.objects.all()}

        # --- 2) Привязываем к Project по project_name_en_out ---
        self.stdout.write("Связывание с Project…")
        if "project_name_en_out" in cols:
            for _, row in df.iterrows():
                proj_name = row.get("project_name_en_out")
                mp_name = row.get("master_project_en_out")
                if pd.isna(proj_name) or pd.isna(mp_name):
                    continue

                proj = Project.objects.filter(
                    english_name__iexact=str(proj_name).strip()
                ).first()
                if proj:
                    proj.master_project = mp_map.get(str(mp_name).strip())
                    proj.save(update_fields=["master_project"])
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Проект не найден: {proj_name!r}")
                    )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Не могу связать Project: нет колонки project_name_en_out."
                )
            )

        # --- 3) Привязываем к MergedRentalTransaction по transaction_id ---
        self.stdout.write("Связывание с MergedRentalTransaction…")
        if "transaction_id" in cols:
            for _, row in df.iterrows():
                tx_id = row.get("transaction_id")
                mp_name = row.get("master_project_en_out")
                if pd.isna(tx_id) or pd.isna(mp_name):
                    continue

                mrt = MergedRentalTransaction.objects.filter(
                    contract_id=str(tx_id).strip()
                ).first()
                if mrt:
                    mrt.master_project = mp_map.get(str(mp_name).strip())
                    mrt.save(update_fields=["master_project"])
                else:
                    self.stdout.write(
                        self.style.WARNING(f"RentalTransaction не найден: {tx_id!r}")
                    )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Не могу связать RentalTransaction: нет колонки transaction_id."
                )
            )

        self.stdout.write(self.style.SUCCESS("Готово."))

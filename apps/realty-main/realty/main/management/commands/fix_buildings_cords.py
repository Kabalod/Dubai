# realty/main/management/commands/fix_buildings_and_coords.py

from django.core.management.base import BaseCommand
from django.db.models import Count
from realty.main.models import Building, Land


class Command(BaseCommand):
    help = (
        "1) Удаляет дубли в Building (один и тот же project + english_name), "
        "оставляя запись с наименьшим PK;\n"
        "2) Заполняет latitude/longitude в Building и Land из связанной Location."
    )

    def handle(self, *args, **options):
        total_deleted = 0
        # 1) Удаляем дубли в Building
        duplicates = (
            Building.objects.values("project_id", "english_name")
            .annotate(cnt=Count("pk"))
            .filter(cnt__gt=1)
        )
        for dup in duplicates:
            qs = Building.objects.filter(
                project_id=dup["project_id"], english_name=dup["english_name"]
            ).order_by("pk")
            # первый (с наименьшим pk) оставляем, остальные удаляем
            keep = qs.first()
            to_delete = qs.exclude(pk=keep.pk)
            cnt = to_delete.count()
            to_delete.delete()
            total_deleted += cnt
            self.stdout.write(
                f"Deleted {cnt} duplicates for project={dup['project_id']} "
                f"english_name='{dup['english_name']}'"
            )
        self.stdout.write(
            self.style.SUCCESS(f"Total duplicates deleted: {total_deleted}")
        )

        # 2) Заполняем координаты в Building
        building_updated = 0
        buildings = Building.objects.select_related("project__location").all()
        for b in buildings:
            loc = getattr(b.project, "location", None)
            if loc and loc.latitude is not None and loc.longitude is not None:
                if b.latitude != loc.latitude or b.longitude != loc.longitude:
                    b.latitude = loc.latitude
                    b.longitude = loc.longitude
                    b.save(update_fields=["latitude", "longitude"])
                    building_updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Buildings updated with coords: {building_updated}")
        )

        # 3) Заполняем координаты в Land
        land_updated = 0
        lands = Land.objects.select_related("project__location").all()
        for l in lands:
            loc = getattr(l.project, "location", None)
            if loc and loc.latitude is not None and loc.longitude is not None:
                if l.latitude != loc.latitude or l.longitude != loc.longitude:
                    l.latitude = loc.latitude
                    l.longitude = loc.longitude
                    l.save(update_fields=["latitude", "longitude"])
                    land_updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Lands updated with coords: {land_updated}")
        )

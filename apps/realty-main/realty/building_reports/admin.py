from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from .models import (
    PFSnapshotBuilding,
    BuildingReportSnapshot,
    AreaReportSnapshot,
)


class SnapshotAdminMixin(admin.ModelAdmin):
    change_list_template = "admin/snapshot_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        urls.insert(
            0,
            path(
                "run-snapshots/",
                self.admin_site.admin_view(self.run_snapshots),
                name=f"run-{self.model._meta.model_name}-snapshots",
            ),
        )
        return urls

    def run_snapshots(self, request):
        self.model.run_snapshot_for_all()
        self.message_user(request, "✅ Снэпшоты пересчитаны")
        return redirect("..")


@admin.register(PFSnapshotBuilding)
class PFSnapshotBuildingAdmin(SnapshotAdminMixin):
    list_display = (
        "building",
        "bedrooms",
        "avg_sale_price",
        "avg_rent_price",
        "median_sale_price",
        "median_rent_price",
        "min_sale_price",
        "max_sale_price",
        "min_rent_price",
        "max_rent_price",
        "avg_exposure_sale",
        "avg_exposure_rent",
        "sale_count",
        "rent_count",
        "ads_per_unit_sale",
        "ads_per_unit_rent",
        "roi",
        "liquidity_sale",
        "liquidity_rent",
    )


@admin.register(BuildingReportSnapshot)
class BuildingReportSnapshotAdmin(SnapshotAdminMixin):
    list_display = (
        "building",
        "number_of_rooms",
        "period_start",
        "period_end",
    )


@admin.register(AreaReportSnapshot)
class AreaReportSnapshotAdmin(SnapshotAdminMixin):
    list_display = (
        "area",
        "number_of_rooms",
        "period_start",
        "period_end",
    )

import csv
import os
import signal
from pathlib import Path
from pyexpat.errors import messages

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse

from .models import Area
from .models import Building
from .models import BuildingLiquidityParameterOne
from .models import DataImport
from .models import Developer
from .models import Function
from .models import Land
from .models import Location
from .models import MergedRentalTransaction
from .models import MergedTransaction
from .models import Project
from .models import Room
from .models import SearchTransactionsLog


class BaseModelAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at", "verified_at")
    list_filter = ("created_at", "updated_at", "verified_at")
    readonly_fields = ("created_at", "updated_at", "verified_at")
    date_hierarchy = "created_at"
    list_per_page = 25


@admin.action(description="Export selected records to CSV")
def export_to_csv(model, _, queryset):
    filename = f"{model.model.__name__}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    fields = [field.name for field in model.model._meta.fields]  # noqa
    writer.writerow(fields)

    for row in queryset.values_list(*fields):
        writer.writerow(row)
    return response


@admin.register(MergedRentalTransaction)
class MergedRentalTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "contract_id",
        "date_of_transaction",
        "building_name",
        "project_name_en",
        "transaction_price",
        "sqm",
        "created_at",
    )
    list_filter = ("date_of_transaction", "building", "project", "area", "is_free_hold")
    search_fields = (
        "contract_id",
        "area_by_pf",
        "building_name",
        "project_name_en",
        "area_name_en",
        "tenant_type_en",
    )
    ordering = ("-date_of_transaction",)
    readonly_fields = ("created_at", "updated_at", "verified_at")

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "date_of_transaction",
                    "contract_id",
                    "contract_reg_type_id",
                    "contract_reg_type_ar",
                    "contract_reg_type_en",
                )
            },
        ),
        (
            "Building & Location",
            {
                "fields": (
                    "building",
                    "project",
                    "area",
                    "building_name",
                    "location_name",
                )
            },
        ),
        (
            "Property Details",
            {
                "fields": (
                    "number_of_rooms",
                    "sqm",
                    "transaction_price",
                    "detail_link",
                    "something_important_v1",
                )
            },
        ),
        (
            "Contract Details",
            {
                "fields": (
                    "contract_start_date",
                    "contract_end_date",
                    "annual_amount",
                    "no_of_prop",
                    "line_number",
                    "is_free_hold",
                )
            },
        ),
        (
            "Ejari & Property Types",
            {
                "fields": (
                    "ejari_bus_property_type_id",
                    "ejari_bus_property_type_ar",
                    "ejari_bus_property_type_en",
                    "ejari_property_type_id",
                    "ejari_property_type_en",
                    "ejari_property_type_ar",
                    "ejari_property_sub_type_id",
                    "ejari_property_sub_type_en",
                    "ejari_property_sub_type_ar",
                )
            },
        ),
        (
            "Usage & Project Info",
            {
                "fields": (
                    "property_usage_en",
                    "property_usage_ar",
                    "project_number",
                    "project_name_ar",
                    "project_name_en",
                    "master_project_ar",
                    "master_project_en",
                )
            },
        ),
        (
            "Area Details",
            {"fields": ("area_id_csv", "area_name_ar", "area_name_en", "actual_area")},
        ),
        (
            "Nearest Landmarks",
            {
                "fields": (
                    "nearest_landmark_ar",
                    "nearest_landmark_en",
                    "nearest_metro_ar",
                    "nearest_metro_en",
                    "nearest_mall_ar",
                    "nearest_mall_en",
                )
            },
        ),
        (
            "Tenant Information",
            {"fields": ("tenant_type_id", "tenant_type_ar", "tenant_type_en")},
        ),
        ("Other", {"fields": ("period", "meter_sale_price")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "verified_at")}),
    )


@admin.register(Developer)
class DeveloperAdmin(BaseModelAdmin):
    list_display = (
        "developer_id",
        "english_name",
        "arabic_name",
        "number",
        "is_followed",
    ) + BaseModelAdmin.list_display
    list_filter = ("is_followed",) + BaseModelAdmin.list_filter
    search_fields = ("english_name", "arabic_name", "number", "developer_id")
    list_editable = ("is_followed",)
    actions = [export_to_csv]


@admin.register(Project)
class ProjectAdmin(BaseModelAdmin):
    list_display = (
        "project_number",
        "english_name",
        "arabic_name",
        "developer",
        "worth",
        "status_en",
        "is_followed",
    ) + ("created_at",)
    list_filter = (
        "is_followed",
        "status_en",
        "developer",
        "main_developer",
    ) + BaseModelAdmin.list_filter
    search_fields = ("project_number", "english_name", "arabic_name", "status_en")
    list_editable = ("is_followed",)
    autocomplete_fields = ("developer", "main_developer")
    actions = [export_to_csv]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "area_idx", "name_en", "name_ar")
    search_fields = ("name_en", "name_ar", "area_idx")
    list_per_page = 25
    actions = [export_to_csv]


@admin.register(Location)
class LocationAdmin(BaseModelAdmin):
    list_display = (
        "id",
        "project",
        "latitude",
        "longitude",
    ) + BaseModelAdmin.list_display
    list_filter = ("project",) + BaseModelAdmin.list_filter
    search_fields = ("project__english_name", "project__arabic_name")
    autocomplete_fields = ("project",)
    actions = [export_to_csv]


@admin.register(Land)
class LandAdmin(BaseModelAdmin):
    list_display = (
        "id",
        "project",
        "english_name",
        "arabic_name",
        "number",
        "property_type",
        "floor_count",
    ) + BaseModelAdmin.list_display
    list_filter = ("property_type", "project") + BaseModelAdmin.list_filter
    search_fields = ("english_name", "arabic_name", "number")
    autocomplete_fields = ("project",)
    actions = [export_to_csv]


@admin.register(Building)
class BuildingAdmin(BaseModelAdmin):
    list_display = (
        "english_name",
        "project",
        "number",
        "property_type",
        "total_units",
        "building_count",
        "area_by_pf",
    ) + ("id",)
    list_filter = ("property_type", "project", "area") + BaseModelAdmin.list_filter
    search_fields = ("english_name", "arabic_name", "number", "property_type")
    autocomplete_fields = ("project", "area")
    actions = [export_to_csv]


@admin.register(Function)
class FunctionAdmin(BaseModelAdmin):
    list_display = ("id", "project", "english_name", "arabic_name") + ("created_at",)
    list_filter = ("project",) + BaseModelAdmin.list_filter
    search_fields = ("english_name", "arabic_name")
    autocomplete_fields = ("project",)
    actions = [export_to_csv]


@admin.register(Room)
class RoomAdmin(BaseModelAdmin):
    list_display = ("id", "function", "english_name", "arabic_name", "value")
    list_filter = ("function",) + BaseModelAdmin.list_filter
    search_fields = ("english_name", "arabic_name", "value")
    autocomplete_fields = ("function",)
    actions = [export_to_csv]


@admin.register(BuildingLiquidityParameterOne)
class BuildingLiquidityParameterOneAdmin(admin.ModelAdmin):
    list_display = ("id", "building", "year", "month", "liquidity_parameter_one")
    list_filter = ("year", "month", "building")
    search_fields = ("building__english_name",)
    actions = [export_to_csv]


@admin.register(MergedTransaction)
class MergedTransactionAdmin(BaseModelAdmin):
    list_display = (
        "transaction_type",
        "building_name",
        "date_of_transaction",
        "transaction_price",
        "sqm",
        "meter_sale_price",
    ) + ("id",)
    list_filter = (
        "transaction_type",
        "date_of_transaction",
        "deal_year",
        "building",
        "area",
    ) + BaseModelAdmin.list_filter
    search_fields = ("building_name", "location_name", "number_of_rooms")
    autocomplete_fields = ("building", "area")
    date_hierarchy = "date_of_transaction"
    actions = [export_to_csv]


@admin.register(SearchTransactionsLog)
class SearchTransactionsLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requested_at",
        "transaction_type",
        "search_substring",
        "avg_price",
        "transaction_count",
        "median_price",
        "avg_price_per_sqft",
        "building_count",
        "total_units",
        "special_liquidity_calc",
    )
    list_filter = ("requested_at", "transaction_type")
    search_fields = ("search_substring",)
    list_per_page = 25
    actions = [export_to_csv]


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "projects_zipfile",
        "clean_data",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "clean_data", "created_at")
    search_fields = ("projects_zipfile", "transactions_file")
    readonly_fields = ("status", "created_at", "updated_at", "error_message")

    actions = ["kill_running_import"]

    @admin.action(description="kill running data import")
    def kill_running_import(self, request, _):
        lockfile = Path("data_import.lock")
        if not lockfile.exists():
            messages.info(request, "No data imported yet.")
            return
        pid = lockfile.read_text().strip()
        os.kill(int(pid), signal.SIGKILL)
        lockfile.unlink()
        DataImport.objects.filter(status="on_going").update(status="cancelled")
        messages.info(request, f"Killed data import with PID {pid}.")


from .models import MasterProject


@admin.register(MasterProject)
class MasterProjecAtdmin(admin.ModelAdmin):
    pass


from .models import CsvImport


@admin.register(CsvImport)
class CsvImportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "status",
        "giper_csv_url",
        "transactions_csv_url",
    )
    readonly_fields = ("created_at", "started_at", "finished_at", "status", "log")
    list_filter = ("status",)
    search_fields = ("giper_csv_url", "transactions_csv_url")


from .models import CsvRentImport


@admin.register(CsvRentImport)
class CsvRentImportAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "rents_csv_url")
    readonly_fields = ("created_at", "started_at", "finished_at", "status", "log")
    list_filter = ("status",)
    search_fields = ("rents_csv_url",)

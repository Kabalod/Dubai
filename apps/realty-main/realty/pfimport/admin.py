# pfimport/admin.py
from django.contrib import admin
from django.contrib import messages

from .models import Area
from .models import Building
from .models import PFJsonUpload
from .models import PFListRent
from .models import PFListSale


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "numeric_area")
    search_fields = ("name",)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "area")
    search_fields = ("name", "area__name")
    list_filter = ("area",)


from django.contrib import admin
from django.utils.html import format_html
from .models import PFListSale, PFListRent


@admin.action(description="Пересчитать ROI для выбранных объявлений")
def recalc_roi_for_queryset(modeladmin, request, queryset):
    count = 0
    for obj in queryset.select_related("building"):
        if obj.building and obj.bedrooms and obj.price:
            # ROI объявления
            avg_rent = getattr(
                obj.building,
                f'avg_rent_{obj.bedrooms if obj.bedrooms != "studio" else "studio"}',
                None,
            )
            if avg_rent and obj.price:
                obj.roi = float(avg_rent) / float(obj.price)
            else:
                obj.roi = 0.0
            # Средний ROI по зданию
            avg_sale = getattr(
                obj.building,
                f'avg_sale_{obj.bedrooms if obj.bedrooms != "studio" else "studio"}',
                None,
            )
            if avg_rent and avg_sale and avg_sale > 0:
                obj.building_avg_roi = float(avg_rent) / float(avg_sale)
            else:
                obj.building_avg_roi = 0.0
            obj.save(update_fields=["roi", "building_avg_roi"])
            count += 1
    messages.success(request, f"ROI пересчитан для {count} объявлений.")


@admin.action(description="Заполнить пустые ROI и Среднее ROI по зданию нулями")
def fill_empty_roi_zero(modeladmin, request, queryset):
    count = 0
    for obj in queryset:
        updated = False
        if obj.roi is None:
            obj.roi = 0.0
            updated = True
        if obj.building_avg_roi is None:
            obj.building_avg_roi = 0.0
            updated = True
        if updated:
            obj.save(update_fields=["roi", "building_avg_roi"])
            count += 1
    messages.success(
        request, f"Обновлено {count} объявлений (roi/building_avg_roi = 0.0)"
    )


@admin.register(PFListSale)
class PFListSaleAdmin(admin.ModelAdmin):
    list_display = ("preview_link", "building", "listing_id", "roi", "building_avg_roi")
    actions = [recalc_roi_for_queryset, fill_empty_roi_zero]

    class Media:
        css = {"all": ("https://unpkg.com/tippy.js@6/dist/tippy.css",)}
        js = (
            "https://unpkg.com/@popperjs/core@2/dist/umd/popper.min.js",
            "https://unpkg.com/tippy.js@6/dist/tippy.umd.min.js",
        )

    @admin.display(description="Preview")
    def preview_link(self, obj):
        shot_url = f"https://api.microlink.io?url={obj.url}&screenshot=true&width=300"
        return format_html(
            '<b> ЗАЙДИ В {id} <a href="{url}" target="_blank" class="preview-link" '
            'data-tippy-content="<img src=\\"{shot}\\" style=\\"max-width:300px;\\"/>">'
            "[Sale #{title}]</a>",
            id=obj.id,
            url=obj.url,
            shot=shot_url,
            title=obj.title or "No title",
        )


@admin.register(PFListRent)
class PFListRentAdmin(admin.ModelAdmin):
    list_display = ("preview_link", "building", "listing_id", "roi", "building_avg_roi")
    actions = [recalc_roi_for_queryset, fill_empty_roi_zero]

    class Media:
        css = PFListSaleAdmin.Media.css
        js = PFListSaleAdmin.Media.js

    @admin.display(description="Preview")
    def preview_link(self, obj):
        shot_url = f"https://api.microlink.io?url={obj.url}&screenshot=true&width=300"
        return format_html(
            '<b> ЗАЙДИ В {id} </b><br> <a href="{url}" target="_blank" class="preview-link" '
            'data-tippy-content="<img src=\\"{shot}\\" style=\\"max-width:300px;\\"/> Перейди по ссылке: '
            "<i>[Rent #{title}]</i></a>",
            id=obj.id,
            url=obj.url,
            shot=shot_url,
            title=obj.title or "No title",
        )


# Регистрация в админке


@admin.register(PFJsonUpload)
class PFJsonUploadAdmin(admin.ModelAdmin):
    list_display = ("id", "upload_file", "created_at")


from .models import PFJsonImport


@admin.register(PFJsonImport)
class PFJsonImportAdmin(admin.ModelAdmin):
    """
    • Создаёте запись → AFTER_CREATE-хук ставит задачу run_pfjson_import
      (ничего вручную нажимать не нужно).
    • На детальной странице видно лог и тайминги.
    """

    # что показываем в списке
    list_display = (
        "id",
        "created_at",
        "started_at",
        "finished_at",
        "status",
        "json_url",
    )
    list_filter = ("status", "wipe_sale_before", "wipe_rent_before")
    search_fields = ("json_url",)
    ordering = ("-created_at",)

    # как расположены поля на форме
    fieldsets = (
        (None, {"fields": ("json_url",)}),
        (
            "Очистить перед импортом",
            {
                "fields": (
                    "wipe_sale_before",
                    "wipe_rent_before",
                    "wipe_area_before",
                    "wipe_buildnig_before",
                )
            },
        ),
        (
            "Только для чтения",
            {
                "fields": (
                    "status",
                    "created_at",
                    "started_at",
                    "finished_at",
                    "log",
                )
            },
        ),
    )
    readonly_fields = (
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "log",
    )


from .models import CommandJob


@admin.register(CommandJob)
class CommandJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "command",
        "status",
        "created_at",
        "started_at",
        "finished_at",
    )
    list_filter = ("status",)
    search_fields = ("command",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("command",)}),
        (
            "Status / Log (read-only)",
            {
                "fields": ("status", "created_at", "started_at", "finished_at", "log"),
            },
        ),
    )
    readonly_fields = ("status", "created_at", "started_at", "finished_at", "log")

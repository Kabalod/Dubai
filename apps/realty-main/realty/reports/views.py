# realty/reports/views.py
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.views import View

from django.db.models import Exists, OuterRef

from realty.pfimport.models import Building
from .models import (
    BuildingReport,
    AreaReport,
    AreaReportDLD,
    CityReport,
    CityReportPF,
    DldBuildingReport,
    BEDROOM_CHOICES,
)
from realty.main.models import Building as DldBuilding


class ReportView(View):
    template_name = "reports/tailwind_report.html"

    # ───── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _pct(curr, prev):
        try:
            if curr is None or prev in (None, 0):
                return None
            return (Decimal(curr) - Decimal(prev)) / Decimal(prev) * 100
        except (InvalidOperation, ZeroDivisionError, TypeError):
            return None

    def _pack_row(
        self,
        label,
        obj_b,
        fld_b_ly,
        fld_b_py,
        obj_a,
        fld_a_ly,
        fld_a_py,
        obj_c,
        fld_c_ly,
        fld_c_py,
        highlight=False,
    ):
        b_ly = getattr(obj_b, fld_b_ly, None) if obj_b else None
        b_py = getattr(obj_b, fld_b_py, None) if obj_b else None
        a_ly = getattr(obj_a, fld_a_ly, None) if obj_a else None
        a_py = getattr(obj_a, fld_a_py, None) if obj_a else None
        c_ly = getattr(obj_c, fld_c_ly, None) if obj_c and fld_c_ly else None
        c_py = getattr(obj_c, fld_c_py, None) if obj_c and fld_c_py else None

        return {
            "label": label,
            "b_val": b_ly,
            "b_pct": self._pct(b_ly, b_py),
            "a_val": a_ly,
            "a_pct": self._pct(a_ly, a_py),
            "c_val": c_ly,
            "c_pct": self._pct(c_ly, c_py),
            "highlight": highlight,
        }

    def get(self, request):
        buildings = Building.objects.filter(dld_building__isnull=False).order_by("name")
        # №from django.db.models import Exists, OuterRef

        # buildings = (
        #     Building.objects
        #     .annotate(has_units=Exists(Unit.objects.filter(building=OuterRef("pk"))))
        #     .filter(has_units=True)        # только здания, у которых есть хотя бы одна Unit
        #     .order_by("name")
        # )
        #  return render(request, self.template_name,, {"buildings": buildings, ...})

        return render(
            request,
            self.template_name,
            {
                "buildings": buildings,
                "bedroom_choices": BEDROOM_CHOICES,
            },
        )

    def post(self, request):
        building_id = request.POST.get("building")
        bedrooms = request.POST.get("bedrooms", "")  # ← всегда строка
        building = get_object_or_404(
            Building, pk=building_id, dld_building__isnull=False
        )

        # если комнатность не выбрана ➜ шаг 2
        if not bedrooms:
            available = BuildingReport.objects.filter(building=building).values_list(
                "bedrooms", flat=True
            )
            # список «код → label» в тех же BEDROOM_CHOICES
            choices = [c for c in BEDROOM_CHOICES if c[0] in available]

            return render(
                request,
                self.template_name,
                {
                    "buildings": Building.objects.filter(
                        dld_building__isnull=False
                    ).order_by("name"),
                    "selected_building": building,
                    "bedroom_choices": choices,  # <— отфильтровано
                    "available_bedrooms": list(available),
                },
            )

        building = get_object_or_404(
            Building, pk=building_id, dld_building__isnull=False
        )

        # Берём уже посчитанные отчёты из базы
        building_report = get_object_or_404(
            BuildingReport, building=building, bedrooms=bedrooms
        )
        area_report = get_object_or_404(
            AreaReport, area=building.area, bedrooms=bedrooms
        )
        city_report = get_object_or_404(CityReport, bedrooms=bedrooms)
        city_report_pf = get_object_or_404(CityReportPF, bedrooms=bedrooms)

        dld_report = get_object_or_404(
            DldBuildingReport, dld_building=building.dld_building, bedrooms=bedrooms
        )

        print(building.dld_building)
        # Снова список для формы
        # buildings = Building.objects.filter(dld_building__isnull=False).order_by("name")

        # --- список зданий для селектора (чтобы не менять template) ---------
        buildings = (  #  <<< NEW >>>
            Building.objects  #  <<< NEW >>>
            #  .filter(dld_building__isnull=False)              #  <<< NEW >>>
            .filter(
                Exists(  #  <<< NEW >>>
                    BuildingReport.objects.filter(  #  <<< NEW >>>
                        building=OuterRef("pk")
                    )  #  <<< NEW >>>
                )
            )  #  <<< NEW >>>
            .select_related("dld_building")  #  <<< NEW >>>
            .order_by("name")  #  <<< NEW >>>
        )

        # Набор метрик для показа годового изменения
        dld_report_metrics = [
            {
                "current": "avg_sale_price_ly",
                "previous": "avg_sale_price_py",
                "label": "Средняя цена продажи",
            },
            {
                "current": "avg_rent_price_ly",
                "previous": "avg_rent_price_py",
                "label": "Средняя цена аренды",
            },
            {
                "current": "avg_sqm_sale_ly",
                "previous": "avg_sqm_sale_py",
                "label": "Средняя площадь продажи",
            },
            {
                "current": "avg_sqm_rent_ly",
                "previous": "avg_sqm_rent_py",
                "label": "Средняя площадь аренды",
            },
            {
                "current": "avg_ppsqm_sale_ly",
                "previous": "avg_ppsqm_sale_py",
                "label": "Цена за кв.м. (продажа)",
            },
            {
                "current": "avg_ppsqm_rent_ly",
                "previous": "avg_ppsqm_rent_py",
                "label": "Цена за кв.м. (аренда)",
            },
            {
                "current": "median_sale_price_ly",
                "previous": "median_sale_price_py",
                "label": "Медианная цена продажи",
            },
            {
                "current": "median_rent_price_ly",
                "previous": "median_rent_price_py",
                "label": "Медианная цена аренды",
            },
            {
                "current": "min_sale_price_ly",
                "previous": "min_sale_price_py",
                "label": "Минимальная цена продажи",
            },
            {
                "current": "max_sale_price_ly",
                "previous": "max_sale_price_py",
                "label": "Максимальная цена продажи",
            },
            {
                "current": "min_rent_price_ly",
                "previous": "min_rent_price_py",
                "label": "Минимальная цена аренды",
            },
            {
                "current": "max_rent_price_ly",
                "previous": "max_rent_price_py",
                "label": "Максимальная цена аренды",
            },
            {
                "current": "count_sale_ly",
                "previous": "count_sale_py",
                "label": "Транзакций продажи",
            },
            {
                "current": "count_rent_ly",
                "previous": "count_rent_py",
                "label": "Транзакций аренды",
            },
            {
                "current": "tx_per_unit_pm_ly",
                "previous": "tx_per_unit_pm_py",
                "label": "Ликвидность продажи (tx/unit/12)",
            },
            {
                "current": "tx_per_unit_pm_ly_rent",
                "previous": "tx_per_unit_pm_py_rent",
                "label": "Ликвидность аренды (tx/unit/12)",
            },
            {"current": "roi_ly", "previous": "roi_py", "label": "ROI"},
        ]

        #       # --- DLD-объекты -------------------------------------------------------
        dld_report = get_object_or_404(
            DldBuildingReport,
            dld_building=building.dld_building,
            bedrooms=bedrooms,
        )
        dld_area_obj = dld_report.dld_building.area  # ← ключевая строка
        area_dld = get_object_or_404(
            AreaReportDLD, area=dld_area_obj, bedrooms=bedrooms
        )
        # "avg_sqm_by_building":        avg_sqm_by_building,      # ★ NEW
        # "avg_ppsqm_by_building":      avg_
        #     # --- таблица «Продажа» -------------------------------------------------
        sale_rows = [
            self._pack_row(
                "площадь",
                dld_report,
                "avg_sqm_sale_ly",
                "avg_sqm_sale_py",
                area_dld,
                "avg_sqm_sale_ly",
                "avg_sqm_sale_py",
                city_report,
                "avg_sqm_by_building",
                "avg_sqm_by_building_py",
                highlight=True,
            ),
            self._pack_row(
                "цена за квадрат",
                dld_report,
                "avg_ppsqm_sale_ly",
                "avg_ppsqm_sale_py",
                area_dld,
                "avg_ppsqm_sale_ly",
                "avg_ppsqm_sale_py",
                city_report,
                "avg_ppsqm_by_building",
                "avg_ppsqm_by_building_py",
                highlight=True,
            ),
            self._pack_row(
                "Средняя в билдинге / br / год",
                dld_report,
                "avg_sale_price_ly",
                "avg_sale_price_py",
                area_dld,
                "avg_price_by_building_ly",
                "avg_price_by_building_py",
                city_report,
                "avg_price_by_building_ly",
                "avg_price_by_building_py",
            ),
            self._pack_row(
                "Медианная в билдинге / br / год",
                dld_report,
                "median_sale_price_ly",
                "median_sale_price_py",
                area_dld,
                "median_sale_price_ly",
                "median_sale_price_py",
                city_report,
                "median_price_ly",
                "median_price_py",
            ),
            self._pack_row(
                "Разброс: Min цен в билдинге / br / год",
                dld_report,
                "min_sale_price_ly",
                "min_sale_price_py",
                area_dld,
                "min_sale_price_ly",
                "min_sale_price_py",
                city_report,
                "min_price_ly",
                "min_price_py",
            ),
            self._pack_row(
                "Разброс: Max цен в билдинге / br / год",
                dld_report,
                "max_sale_price_ly",
                "max_sale_price_py",
                area_dld,
                "max_sale_price_ly",
                "max_sale_price_py",
                city_report,
                "max_price_ly",
                "max_price_py",
            ),
            self._pack_row(
                "Транзакций в билдинге / br : год",
                dld_report,
                "count_sale_ly",
                "count_sale_py",
                area_dld,
                "count_sale_ly",
                "count_sale_py",
                city_report,
                "count_sale_ly",
                "count_sale_py",
            ),
            self._pack_row(
                "Ликвидность (транзакций / кв-р / 12)",
                dld_report,
                "tx_per_unit_pm_ly",
                "tx_per_unit_pm_py",
                area_dld,
                "avg_tx_per_building_ly",
                "avg_tx_per_building_py",
                city_report,
                "avg_sale_per_unit_ratio_ly",
                "avg_sale_per_unit_ratio_py",
                highlight=True,
            ),
            self._pack_row(
                "ROI",
                dld_report,
                "roi_ly",
                "roi_py",
                area_dld,
                "avg_roi_by_building_ly",
                "avg_roi_by_building_py",
                city_report,
                "avg_roi_py",
                "avg_roi_ly",
                highlight=True,
            ),
        ]

        # --- таблица «Аренда» --------------------------------------------------
        rent_rows = [
            self._pack_row(
                "Средняя в билдинге / br / год",
                dld_report,
                "avg_rent_price_ly",
                "avg_rent_price_py",
                area_dld,
                "avg_rent_price_ly",
                "avg_rent_price_py",
                city_report,
                "avg_rent_price_ly",
                "avg_rent_price_py",
            ),
            self._pack_row(
                "цена за квадрат",
                dld_report,
                "avg_ppsqm_rent_ly",
                "avg_ppsqm_rent_py",
                area_dld,
                "avg_ppsqm_rent_ly",
                "avg_ppsqm_rent_py",
                city_report,
                "avg_ppsqm_rent_by_building",
                "avg_ppsqm_rent_by_building_py",
                # None,       None,                None,
                highlight=True,
            ),
            self._pack_row(
                "Медианная в билдинге / br / год",
                dld_report,
                "median_rent_price_ly",
                "median_rent_price_py",
                area_dld,
                "median_rent_price_ly",
                "median_rent_price_py",
                city_report,
                "median_rent_price_ly",
                "median_rent_price_py",
            ),
            self._pack_row(
                "Разброс:Мин цен в билдинге / br / год",
                dld_report,
                "min_rent_price_ly",
                "min_rent_price_py",
                area_dld,
                "min_rent_price_ly",
                "min_rent_price_py",
                city_report,
                "min_rent_price_ly",
                "min_rent_price_py",
            ),
            self._pack_row(
                "Разброс: max цен в билдинге / br / год",
                dld_report,
                "max_rent_price_ly",
                "max_rent_price_py",
                area_dld,
                "max_rent_price_ly",
                "max_rent_price_py",
                city_report,
                "max_rent_price_ly",
                "max_rent_price_py",
            ),
            self._pack_row(
                "Транзакций в билдинге / br : год",
                dld_report,
                "count_rent_ly",
                "count_rent_py",
                area_dld,
                "count_rent_ly",
                "count_rent_py",
                city_report,
                "count_rent_ly",
                "count_rent_py",
            ),
            self._pack_row(
                "Ликвидность аренды (tx / кв-р / 12)",
                dld_report,
                "tx_per_unit_pm_ly_rent",
                "tx_per_unit_pm_py_rent",
                area_dld,
                "avg_tx_per_building_ly_rent",
                "avg_tx_per_building_py_rent",
                None,
                None,
                None,
                highlight=True,
            ),
        ]

        # --- список для формы --------------------------------------------------
        buildings = (
            Building.objects.filter(dld_building__isnull=False)
            .select_related("dld_building")
            .order_by("name")
        )
        ratio = area_report.avg_sale_per_unit_ratio

        ratio_rent = area_report.avg_rent_per_unit_ratio
        #         context = {
        #         "ratio_minus_004": None if ratio is None else ratio - 0.04,
        # }

        # --- контекст ----------------------------------------------------------
        return render(
            request,
            self.template_name,
            {
                "buildings": buildings,
                "bedroom_choices": BEDROOM_CHOICES,
                "selected_building": building,
                "selected_bedrooms": bedrooms,
                "building_report": building_report,
                "area_report": area_report,
                "city_report": city_report,
                "city_report_pf": city_report_pf,
                "dld_report": dld_report,
                # ↓ строки для DLD таблиц
                "dld_sale_rows": sale_rows,
                "dld_rent_rows": rent_rows,
                "ratio_minus_004": None if ratio is None else ratio - 0.002,
                "ratio_minus_005": None if ratio_rent is None else ratio_rent - 0.001,
            },
        )


# from django.shortcuts import render, get_object_or_404
# from .models import DldBuildingReport
# from .forms import DldBuildingReportFilterForm
#
#
# def dldbuilding_report_list(request):
#     form = DldBuildingReportFilterForm(request.GET or None)
#     qs = DldBuildingReport.objects.select_related("dld_building")
#     if form.is_valid():
#         en = form.cleaned_data["english_name"]
#         br = form.cleaned_data["bedrooms"]
#         if en:
#             qs = qs.filter(dld_building__english_name__icontains=en)
#         if br:
#             qs = qs.filter(bedrooms=br)
#     return render(
#         request,
#         "reports/dldbuilding_report_list.html",
#         {
#             "form": form,
#             "reports": qs.order_by("-calculated_at")[:100],  # например, последние 100
#         },
#     )
#
#
# #
#
# import random
#
#
# def dldbuilding_report_detail(request, pk):
#     report = get_object_or_404(
#         DldBuildingReport.objects.select_related("dld_building"), pk=pk
#     )
#
#     # вот поля и подписи (в порядке, как в макете)
#     sale_fields = [
#         ("avg_sqm_sale_ly", "площадь"),
#         ("avg_ppsqm_sale_ly", "цена за квадрат"),
#         ("avg_sale_price_ly", "Средняя в билдинге / br / год"),
#         ("avg_sale_price_py", "прошлый год:"),
#         ("median_sale_price_ly", "Медианная в билдинге / br / год"),
#         ("median_sale_price_py", "прошлый год:"),
#         ("min_sale_price_ly", "Разброс цен в билдинге / br / год: от"),
#         ("max_sale_price_ly", "до"),
#         ("min_sale_price_py", "прошлый год: от"),
#         ("max_sale_price_py", "до"),
#         ("count_sale_ly", "Транзакций в билдинге / br / год:"),
#         ("count_sale_py", "прошлый год:"),
#         ("tx_per_unit_pm_ly", "Ликвидность (tx / units / 12):"),
#         ("tx_per_unit_pm_py", "прошлый год:"),
#         ("roi_ly", "ROI:"),
#         ("roi_py", "прошлый год:"),
#     ]
#
#     rent_fields = [
#         ("avg_rent_price_ly", "Средняя в билдинге / br / год:"),
#         ("avg_rent_price_py", "прошлый год:"),
#         ("avg_sqm_rent_ly", "цена за квадрат:"),
#         ("median_rent_price_ly", "Медианная в билдинге / br / год:"),
#         ("median_rent_price_py", "прошлый год:"),
#         ("min_rent_price_ly", "Разброс цен в билдинге / br / год: от"),
#         ("max_rent_price_ly", "до"),
#         ("min_rent_price_py", "прошлый год: от"),
#         ("max_rent_price_py", "до"),
#         ("count_rent_ly", "Транзакций в билдинге / br / год:"),
#         ("count_rent_py", "прошлый год:"),
#     ]
#
#     # функция-генератор случайных больших и маленьких чисел
#     def make_random_dict(fields):
#         yellow = {name: random.randint(1_000, 1_000_000) for name, _ in fields}
#         change = {name: f"{random.randint(1,100)}%" for name, _ in fields}
#         return yellow, change
#
#     sale_yellow, sale_change = make_random_dict(sale_fields)
#     rent_yellow, rent_change = make_random_dict(rent_fields)
#
#     # собираем sale_rows
#     sale_rows = []
#     for name, label in sale_fields:
#         sale_rows.append(
#             {
#                 "label": label,
#                 "current": getattr(report, name),
#                 "yellow": sale_yellow[name],
#                 "change": sale_change[name],
#                 # для простоты будем дублировать везде одинаковые yellow/change
#                 "yellow_dist": sale_yellow[name],
#                 "change_dist": sale_change[name],
#                 "yellow_dub": sale_yellow[name],
#                 "change_dub": sale_change[name],
#             }
#         )
#
#     # собираем rent_rows
#     rent_rows = []
#     for name, label in rent_fields:
#         rent_rows.append(
#             {
#                 "label": label,
#                 "current": getattr(report, name),
#                 "yellow": rent_yellow[name],
#                 "change": rent_change[name],
#                 "yellow_dist": rent_yellow[name],
#                 "change_dist": rent_change[name],
#                 "yellow_dub": rent_yellow[name],
#                 "change_dub": rent_change[name],
#             }
#         )
#
#     return render(
#         request,
#         "reports/dldbuilding_report_detail.html",
#         {
#             "report": report,
#             "sale_rows": sale_rows,
#             "rent_rows": rent_rows,
#         },
#     )
#
#
# from .models import AreaReportDLD
# from realty.main.models import Area as DldArea
# #
# #
# # views.py
# def area_report_detail(request):
#     areas = DldArea.objects.all()
#     bedroom_choices = BEDROOM_CHOICES
#
#     selected_area = None
#     selected_bedrooms = None
#     report = None
#
#     area_pk = request.GET.get("area")
#     br = request.GET.get("bedrooms")
#     if area_pk and br:
#         selected_area = get_object_or_404(DldArea, pk=area_pk)
#         selected_bedrooms = br
#         # ТОЛЬКО ЧИТАЕМ из БД, не пересчитываем
#         report = AreaReportDLD.objects.filter(
#             area=selected_area, bedrooms=selected_bedrooms
#         ).first()
#
#     return render(
#         request,
#         "reports/area_report_detail.html",
#         {
#             "areas": areas,
#             "bedroom_choices": bedroom_choices,
#             "selected_area": selected_area,
#             "selected_bedrooms": selected_bedrooms,
#             "report": report,
#         },
#     )
#
#
# # realty/reports/views.py  ← добавьте в конец
#
# from django.http import JsonResponse
# from django.forms.models import model_to_dict
# from django.views.decorators.http import require_GET
#
#
# # ------------------------------------------------------------------
# # 1. Сводный отчёт по building/area/city/dld
# #    GET /reports/api/aggregated/?building=<id>&bedrooms=<br>
# # ------------------------------------------------------------------
# @require_GET
# def aggregated_report_api(request):
#     building_id = request.GET.get("building")
#     bedrooms = request.GET.get("bedrooms")
#
#     if not (building_id and bedrooms):
#         return JsonResponse(
#             {"detail": "`building` и `bedrooms` обязательны."},
#             status=400,
#         )
#
#     building = get_object_or_404(Building, pk=building_id, dld_building__isnull=False)
#     building_report = get_object_or_404(
#         BuildingReport, building=building, bedrooms=bedrooms
#     )
#     area_report = get_object_or_404(AreaReport, area=building.area, bedrooms=bedrooms)
#     city_report = get_object_or_404(CityReport, bedrooms=bedrooms)
#     dld_report = get_object_or_404(
#         DldBuildingReport,
#         dld_building=building.dld_building,
#         bedrooms=bedrooms,
#     )
#
#     return JsonResponse(
#         {
#             "building": model_to_dict(building, fields=["id", "name", "area_id"]),
#             "bedrooms": bedrooms,
#             "building_report": model_to_dict(
#                 building_report, exclude=["id", "building"]
#             ),
#             "area_report": model_to_dict(area_report, exclude=["id", "area"]),
#             "city_report": model_to_dict(city_report, exclude=["id"]),
#             "dld_report": model_to_dict(dld_report, exclude=["id", "dld_building"]),
#         },
#         json_dumps_params={"ensure_ascii": False},
#     )
#
#
# # ------------------------------------------------------------------
# # 2. Список DLD-отчётов
# #    GET /reports/api/dldbuilding/?english_name=<str>&bedrooms=<br>
# # ------------------------------------------------------------------
# @require_GET
# def dldbuilding_report_list_api(request):
#     qs = DldBuildingReport.objects.select_related("dld_building")
#     en = request.GET.get("english_name")
#     br = request.GET.get("bedrooms")
#
#     if en:
#         qs = qs.filter(dld_building__english_name__icontains=en)
#     if br:
#         qs = qs.filter(bedrooms=br)
#
#     data = [
#         {
#             "id": r.pk,
#             "calculated_at": r.calculated_at,
#             "bedrooms": r.bedrooms,
#             "dld_building": {
#                 "id": r.dld_building_id,
#                 "english_name": r.dld_building.english_name,
#             },
#             # — при необходимости выводите любые поля модели —
#             "avg_sale_price_ly": r.avg_sale_price_ly,
#             "avg_rent_price_ly": r.avg_rent_price_ly,
#         }
#         for r in qs.order_by("-calculated_at")[:100]
#     ]
#     return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})
#
#
# # ------------------------------------------------------------------
# # 3. Детальный DLD-отчёт
# #    GET /reports/api/dldbuilding/<pk>/
# # ------------------------------------------------------------------
# @require_GET
# def dldbuilding_report_detail_api(request, pk):
#     report = get_object_or_404(
#         DldBuildingReport.objects.select_related("dld_building"), pk=pk
#     )
#     data = model_to_dict(report, exclude=["id"])
#     data["dld_building"] = {
#         "id": report.dld_building_id,
#         "english_name": report.dld_building.english_name,
#     }
#     return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
#
#
# # ------------------------------------------------------------------
# # 4. Отчёт по Area
# #    GET /reports/api/area/?area=<id>&bedrooms=<br>
# # ------------------------------------------------------------------
# @require_GET
# def area_report_detail_api(request):
#     area_pk = request.GET.get("area")
#     br = request.GET.get("bedrooms")
#
#     if not (area_pk and br):
#         return JsonResponse(
#             {"detail": "`area` и `bedrooms` обязательны."},
#             status=400,
#         )
#
#     area = get_object_or_404(DldArea, pk=area_pk)
#     report = AreaReportDLD.objects.filter(area=area, bedrooms=br).first()
#     if report is None:
#         return JsonResponse({"detail": "Отчёт не найден."}, status=404)
#
#     data = model_to_dict(report, exclude=["id", "area"])
#     data["area"] = {"id": area.pk, "english_name": area.name_en}
#     return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
#
#
# class CombinedReportView(View):
#     template_name = "reports/combined_report.html"
#
#     def get(self, request):
#         return render(
#             request,
#             self.template_name,
#             {
#                 "buildings": Building.objects.filter(
#                     dld_building__isnull=False
#                 ).order_by("name"),
#                 "areas": DldArea.objects.order_by("name_en"),
#                 "bedroom_choices": BEDROOM_CHOICES,
#             },
#         )

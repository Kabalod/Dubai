# realty/reports/views.py

from django.shortcuts import render, get_object_or_404
from django.views import View

from realty.pfimport.models import Building
from .models import (
    BuildingReport,
    AreaReport,
    CityReport,
    DldBuildingReport,
    BEDROOM_CHOICES,
)
from realty.main.models import Building as DldBuilding

from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views.decorators.http import require_GET


from .models import AreaReportDLD
from realty.main.models import Area as DldArea


class CombinedReportView2(View):
    template_name = "reports/combined_report2.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "buildings": Building.objects.filter(
                    dld_building__isnull=False
                ).order_by("name"),
                "areas": DldArea.objects.order_by("name_en"),
                "bedroom_choices": BEDROOM_CHOICES,
            },
        )


SALE_FIELDS = [
    ("avg_sqm_sale_ly", "площадь"),
    ("avg_ppsqm_sale_ly", "цена за квадрат"),
    ("avg_sale_price_ly", "Средняя в билдинге / br / год"),
    ("avg_sale_price_py", "прошлый год:"),
    ("median_sale_price_ly", "Медианная в билдинге / br / год"),
    ("median_sale_price_py", "прошлый год:"),
    ("min_sale_price_ly", "Разброс цен в билдинге / br / год: от"),
    ("max_sale_price_ly", "до"),
    ("min_sale_price_py", "прошлый год: от"),
    ("max_sale_price_py", "до"),
    ("count_sale_ly", "Транзакций в билдинге / br / год:"),
    ("count_sale_py", "прошлый год:"),
    ("tx_per_unit_pm_ly", "Ликвидность (tx / units / 12):"),
    ("tx_per_unit_pm_py", "прошлый год:"),
    ("roi_ly", "ROI:"),
    ("roi_py", "прошлый год:"),
]

RENT_FIELDS = [
    ("avg_rent_price_ly", "Средняя в билдинге / br / год:"),
    ("avg_rent_price_py", "прошлый год:"),
    ("avg_sqm_rent_ly", "цена за квадрат:"),
    ("median_rent_price_ly", "Медианная в билдинге / br / год:"),
    ("median_rent_price_py", "прошлый год:"),
    ("min_rent_price_ly", "Разброс цен в билдинге / br / год: от"),
    ("max_rent_price_ly", "до"),
    ("min_rent_price_py", "прошлый год: от"),
    ("max_rent_price_py", "до"),
    ("count_rent_ly", "Транзакций в билдинге / br / год:"),
    ("count_rent_py", "прошлый год:"),
]
#
# def _make_row_dict(report, fields):
#     """Преобразуем (field, label) → {"label":…, "current":…, …}"""
#     rows = []
#     for fname, label in fields:
#         curr = getattr(report, fname)
#         # Для Δ возьмём однофамильные LY/PY, если оба есть
#         if fname.endswith("_ly"):
#             base = fname[:-3]
#             ly   = curr
#             py   = getattr(report, base + "_py", None)
#             chg  = f"{round((ly - py) / py * 100, 2)}%" if ly and py else None
#         else:
#             chg = None
#         rows.append({"label": label, "current": curr, "change": chg})
#     return rows
#
# @require_GET
# def dldbuilding_report_rows_api(request):
#     building_id = request.GET.get("building")
#     bedrooms    = request.GET.get("bedrooms")
#     if not (building_id and bedrooms):
#         return JsonResponse({"detail": "`building` и `bedrooms` обязательны."}, status=400)
#
#     building = get_object_or_404(Building, pk=building_id, dld_building__isnull=False)
#     report   = get_object_or_404(
#         DldBuildingReport,
#         dld_building=building.dld_building,
#         bedrooms=bedrooms,
#     )
#
#     data = {
#         "sale_rows": _make_row_dict(report, SALE_FIELDS),
#         "rent_rows": _make_row_dict(report, RENT_FIELDS),
#         "last_3_sales": [
#             {"date": tx.date, "price": tx.price, "sqm": tx.sqm}
#             for tx in getattr(report, "last_3_sales", [])[:3]
#         ],
#         "last_3_rents": [
#             {"date": tx.date, "price": tx.price, "sqm": tx.sqm}
#             for tx in getattr(report, "last_3_rents", [])[:3]
#         ],
#     }
#     return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
# realty/reports/views.py
from math import isfinite


def _safe_percent(curr, prev):
    try:
        if prev not in (None, 0) and curr not in (None,):
            pct = (curr - prev) / prev * 100
            return round(pct, 2) if isfinite(pct) else None
    except Exception:
        pass
    return None


def _make_row_dict(report, fields):
    rows = []
    for fname, label in fields:
        curr = getattr(report, fname)
        row = {
            "label": label,
            "current": curr,
            # заполняем «цветные» колонки placeholders-ами — фронт всё равно их не
            # использует сейчас, но пусть будут, чтобы JS не падал
            "yellow_dist": None,
            "change_dist": None,
            "yellow_dub": None,
            "change_dub": None,
        }
        if fname.endswith("_ly"):
            base = fname[:-3]
            prev = getattr(report, base + "_py", None)
            row["prev"] = prev
            row["change"] = _safe_percent(curr, prev)
        else:
            row["prev"] = None
            row["change"] = None
        rows.append(row)
    return rows


@require_GET
def dldbuilding_report_rows_api(request):
    building_id = request.GET.get("building")
    bedrooms = request.GET.get("bedrooms")
    if not (building_id and bedrooms):
        return JsonResponse(
            {"detail": "`building` и `bedrooms` обязательны."}, status=400
        )

    building = get_object_or_404(Building, pk=building_id, dld_building__isnull=False)
    report = get_object_or_404(
        DldBuildingReport,
        dld_building=building.dld_building,
        bedrooms=bedrooms,
    )

    return JsonResponse(
        {
            "sale_rows": _make_row_dict(report, SALE_FIELDS),
            "rent_rows": _make_row_dict(report, RENT_FIELDS),
            "last_3_sales": [
                {"date": tx.date, "price": tx.price, "sqm": tx.sqm}
                for tx in getattr(report, "last_3_sales", [])[:3]
            ],
            "last_3_rents": [
                {"date": tx.date, "price": tx.price, "sqm": tx.sqm}
                for tx in getattr(report, "last_3_rents", [])[:3]
            ],
        },
        json_dumps_params={"ensure_ascii": False},
    )

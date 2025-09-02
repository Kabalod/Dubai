"""
/experiments/  — отчёт по одному зданию + все сравнительные метрики
"""

import numpy as np
from django.db.models import Avg
from django.db.models import Q
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from realty.main.models import Building as DldBuilding
from realty.main.models import BuildingLiquidityParameterOne
from realty.main.models import MergedRentalTransaction
from realty.main.models import MergedTransaction
from realty.main.stats import calc_and_save_search_log

from .forms import BuildingReportForm
from .models import Building as PFBuilding
from .models import PFListRent
from .models import PFListSale


def building_report_view(request):
    """
    Страница «Отчёт по зданию».
    Период – фиксировано 2 года, тип сделок – sales.
    """
    result = None

    if request.method == "POST":
        form = BuildingReportForm(request.POST)
        if form.is_valid():
            building = form.cleaned_data["building"]

            # считаем метрики
            result = calc_and_save_search_log(
                transaction_type="rent",  # фиксированно
                search_substring=building.english_name,
                property_components=None,
                period_str="1 year",  # фиксированно
                return_dict=True,
                use_cache=True,
            )
    else:
        form = BuildingReportForm()

    return render(
        request,
        "pfimport/building_report.html",
        {"form": form, "result": result, "period": "1 year"},
    )


# ───────────────────── DLD BUILDING (raw) ─────────────────────


def _stats_dld_building(dld_bld: DldBuilding, bedrooms: str) -> dict:
    sale_qs = MergedTransaction.objects.filter(
        transaction_type="sales", building=dld_bld, number_of_rooms=bedrooms
    )
    rent_qs = MergedRentalTransaction.objects.filter(
        building=dld_bld, number_of_rooms=bedrooms
    )

    sale = _stats_dld(sale_qs)
    rent = _stats_dld(rent_qs)

    # total units
    total_units = dld_bld.total_units or (
        dld_bld.project.total_units if dld_bld.project else 0
    )

    # -------- Liquidity ----------
    sale_liq_raw = _safe_div(sale["count"], total_units)
    sale_liq_pct = (
        _safe_div(sale_liq_raw, 12) * 100 if sale_liq_raw is not None else None
    )

    rent_liq_raw = _safe_div(rent["count"], total_units)
    rent_liq_pct = (
        _safe_div(rent_liq_raw, 12) * 100 if rent_liq_raw is not None else None
    )

    # -------- ROI ----------
    roi_pct = _safe_div(rent["avg"], sale["avg"])
    roi_pct = roi_pct * 100 if roi_pct else None

    # Liquidity parameter-1 (если есть)
    liq_param = (
        BuildingLiquidityParameterOne.objects.filter(building=dld_bld).aggregate(
            avg=Avg("liquidity_parameter_one")
        )
    )["avg"]

    return dict(
        sale=sale,
        rent=rent,
        roi_pct=roi_pct,
        sale_liq_pct=sale_liq_pct,
        rent_liq_pct=rent_liq_pct,
        liq_param_one=liq_param,
        total_units=total_units,
    )


# ───────────────────────── helpers ─────────────────────────
def _safe_div(a, b):
    try:
        return a / b if a and b else None
    except ZeroDivisionError:
        return None


def _stats_pf(qs):
    prices = [float(p) for p in qs.values_list("price", flat=True) if p]
    areas = [float(a) for a in qs.values_list("numeric_area", flat=True) if a]
    ppsqm = [p / a for p, a in zip(prices, areas, strict=False) if a]
    if not prices:
        return dict(
            avg=None,
            median=None,
            min=None,
            max=None,
            spread=None,
            count=0,
            avg_ppsqm=None,
        )
    return dict(
        avg=np.mean(prices),
        median=np.median(prices),
        min=min(prices),
        max=max(prices),
        spread=max(prices) - min(prices),
        count=len(prices),
        avg_ppsqm=np.mean(ppsqm) if ppsqm else None,
    )


def _stats_dld(qs):
    prices = [float(p) for p in qs.values_list("transaction_price", flat=True) if p]
    areas = [float(a) for a in qs.values_list("sqm", flat=True) if a]
    ppsqm = [p / a for p, a in zip(prices, areas, strict=False) if a]
    if not prices:
        return dict(
            avg=None,
            median=None,
            min=None,
            max=None,
            spread=None,
            count=0,
            avg_ppsqm=None,
        )
    return dict(
        avg=np.mean(prices),
        median=np.median(prices),
        min=min(prices),
        max=max(prices),
        spread=max(prices) - min(prices),
        count=len(prices),
        avg_ppsqm=np.mean(ppsqm) if ppsqm else None,
    )


def _trend(qs, price_field):
    if not qs.exists():
        return [], []
    ann = "added_on" if price_field == "price" else "date_of_transaction"
    rows = (
        qs.annotate(y=ExtractYear(ann))
        .values("y")
        .annotate(a=Avg(price_field))
        .order_by("y")
    )
    return [r["y"] for r in rows], [round(r["a"], 1) for r in rows]


def _pf_buildings_qs():
    return (
        PFBuilding.objects.filter(
            Q(pflistsale__isnull=False)
            | Q(pflistrent__isnull=False)
            | Q(dld_building__mergedtransaction__isnull=False)
            | Q(dld_building__mergedrentaltransaction__isnull=False)
        )
        .distinct()
        .order_by("name")
    )


# ───────────────────────── view ─────────────────────────
def building_full_metrics_view(request):
    buildings = _pf_buildings_qs()
    br_choices = [("studio", "Studio"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4+")]
    bld_id = request.GET.get("building")
    br = request.GET.get("bedrooms", "1")

    # базовый context
    ctx = dict(
        buildings=buildings,
        bedrooms_choices=br_choices,
        selected_building_id=bld_id,
        selected_bedrooms=br,
        metrics=None,
    )

    # форма без выбора
    if not bld_id:
        return render(request, "pfimport/full_building_metrics.html", ctx)

    bld = get_object_or_404(PFBuilding, pk=bld_id)
    area = bld.area
    dld_bld: DldBuilding | None = bld.dld_building

    # PF queryset-ы
    pf_sale_bld = PFListSale.objects.filter(building=bld, bedrooms=br)
    pf_rent_bld = PFListRent.objects.filter(building=bld, bedrooms=br)
    pf_sale_area = PFListSale.objects.filter(building__area=area, bedrooms=br)
    pf_rent_area = PFListRent.objects.filter(building__area=area, bedrooms=br)
    pf_sale_city = PFListSale.objects.filter(bedrooms=br)
    pf_rent_city = PFListRent.objects.filter(bedrooms=br)

    # DLD queryset-ы
    if dld_bld:
        dld_sale_bld = MergedTransaction.objects.filter(
            transaction_type="sales", building=dld_bld, number_of_rooms=br
        )
        dld_rent_bld = MergedRentalTransaction.objects.filter(
            building=dld_bld, number_of_rooms=br
        )
        if dld_bld.area:
            dld_sale_area = MergedTransaction.objects.filter(
                transaction_type="sales",
                building__area=dld_bld.area,
                number_of_rooms=br,
            )
            dld_rent_area = MergedRentalTransaction.objects.filter(
                building__area=dld_bld.area, number_of_rooms=br
            )
        else:
            dld_sale_area = dld_rent_area = MergedTransaction.objects.none()
    else:
        dld_sale_bld = dld_rent_bld = dld_sale_area = dld_rent_area = (
            MergedTransaction.objects.none()
        )

    dld_sale_city = MergedTransaction.objects.filter(
        transaction_type="sales", number_of_rooms=br
    )
    dld_rent_city = MergedRentalTransaction.objects.filter(number_of_rooms=br)

    # статистика
    pf_sale_bld_s, pf_rent_bld_s = _stats_pf(pf_sale_bld), _stats_pf(pf_rent_bld)
    pf_sale_area_s, pf_rent_area_s = _stats_pf(pf_sale_area), _stats_pf(pf_rent_area)
    pf_sale_city_s, pf_rent_city_s = _stats_pf(pf_sale_city), _stats_pf(pf_rent_city)

    dld_sale_bld_s, dld_rent_bld_s = _stats_dld(dld_sale_bld), _stats_dld(dld_rent_bld)
    dld_sale_area_s, dld_rent_area_s = (
        _stats_dld(dld_sale_area),
        _stats_dld(dld_rent_area),
    )
    dld_sale_city_s, dld_rent_city_s = (
        _stats_dld(dld_sale_city),
        _stats_dld(dld_rent_city),
    )

    # доп-метрики
    pf_total_flats = dld_bld.total_units if dld_bld and dld_bld.total_units else None
    pf_sale_flats = sum(
        [
            bld.sale_count_studio,
            bld.sale_count_1br,
            bld.sale_count_2br,
            bld.sale_count_3br,
            bld.sale_count_4br,
        ]
    )
    pf_units_br = {
        "studio": bld.sale_count_studio,
        "1": bld.sale_count_1br,
        "2": bld.sale_count_2br,
        "3": bld.sale_count_3br,
        "4": bld.sale_count_4br,
    }.get(br, 0)

    pf_sale_exp = _safe_div(
        bld.sum_exposure_sale_days, bld.numbers_of_processed_sale_ads
    )
    pf_rent_exp = _safe_div(
        bld.sum_exposure_rent_days, bld.numbers_of_processed_rent_ads
    )

    pf_roi = _safe_div(pf_rent_bld_s["avg"], pf_sale_bld_s["avg"])
    dld_roi = _safe_div(dld_rent_bld_s["avg"], dld_sale_bld_s["avg"])

    liq_raw = _safe_div(dld_sale_bld_s["count"], pf_total_flats)
    liquidity = _safe_div(liq_raw, 12) if liq_raw is not None else None

    # тренды
    pf_sale_lbl, pf_sale_val = _trend(pf_sale_bld, "price")
    pf_rent_lbl, pf_rent_val = _trend(pf_rent_bld, "price")
    dld_sale_lbl, dld_sale_val = _trend(dld_sale_bld, "transaction_price")
    dld_rent_lbl, dld_rent_val = _trend(dld_rent_bld, "transaction_price")

    # последние сделки
    pf_sale_last = list(pf_sale_bld.order_by("-added_on")[:3])
    pf_rent_last = list(pf_rent_bld.order_by("-added_on")[:3])
    dld_sale_last = list(dld_sale_bld.order_by("-date_of_transaction")[:3])
    dld_rent_last = list(dld_rent_bld.order_by("-date_of_transaction")[:3])
    # ───── RAW DLD-building block (новое) ─────
    dld_raw = _stats_dld_building(dld_bld, br) if dld_bld else None

    ctx["metrics"] = dict(
        br=br,
        building_name=bld.name,
        # объёмы
        flats_total=pf_total_flats,
        flats_sale=pf_sale_flats,
        flats_br=pf_units_br,
        # PF SALE
        pf_sale=pf_sale_bld_s,
        pf_rent=pf_rent_bld_s,
        pf_sale_exp=pf_sale_exp,
        pf_rent_exp=pf_rent_exp,
        # AREA & CITY для PF
        pf_sale_area=pf_sale_area_s,
        pf_rent_area=pf_rent_area_s,
        pf_sale_city=pf_sale_city_s,
        pf_rent_city=pf_rent_city_s,
        # DLD
        dld_sale=dld_sale_bld_s,
        dld_rent=dld_rent_bld_s,
        dld_sale_area=dld_sale_area_s,
        dld_rent_area=dld_rent_area_s,
        dld_sale_city=dld_sale_city_s,
        dld_rent_city=dld_rent_city_s,
        # ROI & Liquidity
        pf_roi=pf_roi * 100 if pf_roi else None,
        dld_roi=dld_roi * 100 if dld_roi else None,
        liquidity=liquidity * 100 if liquidity else None,
        # графики
        pf_sale_lbl=pf_sale_lbl,
        pf_sale_val=pf_sale_val,
        pf_rent_lbl=pf_rent_lbl,
        pf_rent_val=pf_rent_val,
        dld_sale_lbl=dld_sale_lbl,
        dld_sale_val=dld_sale_val,
        dld_rent_lbl=dld_rent_lbl,
        dld_rent_val=dld_rent_val,
        # последние сделки
        pf_sale_last=pf_sale_last,
        pf_rent_last=pf_rent_last,
        dld_sale_last=dld_sale_last,
        dld_rent_last=dld_rent_last,
    )
    ctx["metrics"]["dld_raw"] = dld_raw
    return render(request, "pfimport/full_building_metrics.html", ctx)

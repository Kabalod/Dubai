import datetime

from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Q
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from .models import Area
from .models import Building
from .models import PFListRent
from .models import PFListSale


def building_report_view(request, building_id):
    """
    Рендерит «умный отчёт» по одному Building:
      1) Input Data
      2) Summary (sale + rent KPI)
      3) Apartment analytics (тренды + недавние сделки)
      4) Rent analytics (аналогично)
      5) Building info + графики
      6) Developer info + график
    """
    # 1. Основные объекты
    bld = get_object_or_404(Building, pk=building_id)
    bedrooms = request.GET.get("bedrooms", "1")
    today = datetime.date.today()

    # 2. Input Data — усреднённая цена и площадь для этого здания/типа
    sale_qs_bld = PFListSale.objects.filter(
        building=bld, bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
    )
    input_agg = sale_qs_bld.aggregate(
        avg_price=Avg("price"), avg_area=Avg("numeric_area")
    )
    input_price = input_agg["avg_price"] or 0
    input_area = input_agg["avg_area"] or 0

    # 3. Summary — Purchase/Sale KPI
    #    Price per sqm: You vs Building vs District vs Dubai
    #    Growth, Offer, Demand, Liquidity можно сделать по аналогии
    def avg_ppsqm(qs):
        return (
            qs.annotate(ppsqm=F("price") / F("numeric_area")).aggregate(
                avg_ppsqm=Avg("ppsqm", output_field=FloatField())
            )["avg_ppsqm"]
            or 0
        )

    you_ppsqm = (input_price / input_area) if input_area else 0
    bld_ppsqm = avg_ppsqm(sale_qs_bld)
    district_ppsqm = avg_ppsqm(
        PFListSale.objects.filter(
            building__area=bld.area,
            bedrooms=bedrooms,
            price__isnull=False,
            numeric_area__gt=0,
        )
    )
    city_ppsqm = avg_ppsqm(
        PFListSale.objects.filter(
            bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
        )
    )

    summary_sale = {
        "price": {
            "you": round(you_ppsqm, 2),
            "building": round(bld_ppsqm, 2),
            "district": round(district_ppsqm, 2),
            "dld": round(city_ppsqm, 2),
        },
        # можно добавить growth/offer/demand/liquidity
    }

    # 4. Apartment analytics — тренды средних ppsqm по годам
    def get_trend(qs):
        rows = (
            qs.annotate(year=ExtractYear("added_on"))
            .values("year")
            .annotate(
                avg_ppsqm=Avg(F("price") / F("numeric_area"), output_field=FloatField())
            )
            .order_by("year")
        )
        years = [r["year"] for r in rows]
        data = [round(r["avg_ppsqm"] or 0, 2) for r in rows]
        return years, data

    sale_all_city = PFListSale.objects.filter(
        bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
    )
    sale_all_area = sale_all_city.filter(building__area=bld.area)
    years, data_city = get_trend(sale_all_city)
    _, data_area = get_trend(sale_all_area)
    _, data_bld = get_trend(sale_qs_bld)

    # Recent Deals — последние 5 продаж
    recent_deals = sale_qs_bld.order_by("-added_on")[:5]

    # 5. Rent analytics (аналогично sale, но по PFListRent)
    rent_qs_bld = PFListRent.objects.filter(
        building=bld, bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
    )
    rent_you_ppsqm = round(
        (
            rent_qs_bld.aggregate(
                avg_ppsqm=Avg(F("price") / F("numeric_area"), output_field=FloatField())
            )["avg_ppsqm"]
            or 0
        ),
        2,
    )
    rent_bld_ppsqm = rent_you_ppsqm
    rent_district_ppsqm = round(
        (
            PFListRent.objects.filter(
                building__area=bld.area,
                bedrooms=bedrooms,
                price__isnull=False,
                numeric_area__gt=0,
            )
            .annotate(ppsqm=F("price") / F("numeric_area"))
            .aggregate(avg_ppsqm=Avg("ppsqm", output_field=FloatField()))["avg_ppsqm"]
            or 0
        ),
        2,
    )
    rent_city_ppsqm = round(
        (
            PFListRent.objects.filter(
                bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
            )
            .annotate(ppsqm=F("price") / F("numeric_area"))
            .aggregate(avg_ppsqm=Avg("ppsqm", output_field=FloatField()))["avg_ppsqm"]
            or 0
        ),
        2,
    )

    summary_rent = {
        "price": {
            "you": rent_you_ppsqm,
            "building": rent_bld_ppsqm,
            "district": rent_district_ppsqm,
            "dld": rent_city_ppsqm,
        },
        # ROI, growth, offer, demand, liquidity...
    }
    years_rent, data_rent_city = get_trend(
        PFListRent.objects.filter(
            bedrooms=bedrooms, price__isnull=False, numeric_area__gt=0
        )
    )
    _, data_rent_area = get_trend(
        PFListRent.objects.filter(
            building__area=bld.area,
            bedrooms=bedrooms,
            price__isnull=False,
            numeric_area__gt=0,
        )
    )
    _, data_rent_bld = get_trend(rent_qs_bld)
    recent_rent_deals = rent_qs_bld.order_by("-added_on")[:5]

    # 6. Building info + charts: service charge, floors, unit mix, commissioning usw.
    building_info = {
        "service_charge": getattr(bld, "service_charge", "—"),
        "num_units": bld.sale_count_1br
        + bld.sale_count_2br
        + bld.sale_count_3br
        + bld.sale_count_4br,
        "num_floors": getattr(bld, "numbers_of_processed_sale_ads", "—"),
        "year_built": bld.area.avg_days_on_market,  # пример
        "developer": bld.area.name,
    }

    # 7. Developer info
    dev_name = bld.area.name
    dev_buildings = Building.objects.filter(area__name=dev_name)
    dev_info = {
        "num_buildings": dev_buildings.count(),
        "avg_ppsqm": round(
            dev_buildings.annotate(
                ppsqm=F("sale_sum_studio") / F("sale_count_studio")
            ).aggregate(avg=Avg("ppsqm", output_field=FloatField()))["avg"]
            or 0,
            2,
        ),
    }

    # Рендерим
    return render(
        request,
        "pfimport/building_report.html",
        {
            "building": bld,
            "bedrooms": bedrooms,
            "today": today,
            "input_price": input_price,
            "input_area": input_area,
            "summary_sale": summary_sale,
            "years": years,
            "data_city": data_city,
            "data_area": data_area,
            "data_bld": data_bld,
            "recent_deals": recent_deals,
            "summary_rent": summary_rent,
            "years_rent": years_rent,
            "data_rent_city": data_rent_city,
            "data_rent_area": data_rent_area,
            "data_rent_bld": data_rent_bld,
            "recent_rent_deals": recent_rent_deals,
            "building_info": building_info,
            "dev_info": dev_info,
        },
    )


def _serialize_marker(obj, kind: str) -> dict:
    return {
        "id": obj.id,
        "kind": kind,  # "sale" | "rent"
        "title": obj.title
        or obj.display_address
        or f"{kind.title()} #{obj.listing_id}",
        "price": float(obj.price) if obj.price else None,
        "lat": obj.latitude,
        "lng": obj.longitude,
    }


def _markers_from_page(page_obj, kind):
    markers = []
    for row in page_obj:
        obj = row["obj"]
        if obj.latitude and obj.longitude:
            markers.append(_serialize_marker(obj, kind))
    return markers


def pf_listings_sale_view(request):
    context, page_obj = _build_common(request, PFListSale, list_type="sale")
    context["map_markers"] = _markers_from_page(page_obj, "sale")
    return render(request, "pfimport/pf_listings_table.html", context)


def pf_listings_rent_view(request):
    context, page_obj = _build_common(request, PFListRent, list_type="rent")
    context["map_markers"] = _markers_from_page(page_obj, "rent")
    return render(request, "pfimport/pf_listings_table.html", context)


def _build_common(request, model_cls, *, list_type: str):
    # GET‑параметры
    q = request.GET.get("q", "").strip()
    filter_area = request.GET.get("area", "").strip()
    # pf_roi_min_str = request.GET.get("pf_avg_roi_min", "").strip()
    # pf_roi_max_str = request.GET.get("pf_avg_roi_max", "").strip()
    # ▼▼▼ заменили ROI-фильтры на price-фильтры ▼▼▼
    price_min_str = request.GET.get("price_min", "").strip()
    price_max_str = request.GET.get("price_max", "").strip()

    sort_field = request.GET.get("sort", "").strip()
    sort_order = request.GET.get("order", "asc").lower()
    page_number = request.GET.get("page", "1")

    # QS: только районы с непустым verified_value
    qs = model_cls.objects.filter(area__verified_value__isnull=False).exclude(
        area__verified_value__exact=""
    )

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(display_address__icontains=q))
    if filter_area:
        qs = qs.filter(display_address__icontains=filter_area)

    today = datetime.date.today()
    raw_list = []

    def parse_addr(addr):
        parts = [x.strip() for x in (addr or "").split(",")]
        while len(parts) < 4:
            parts.append("")
        return parts[:4]

    for obj in qs:
        address1, _, address3, _ = parse_addr(obj.display_address)
        days_on_market = (today - obj.added_on.date()).days if obj.added_on else None
        price_per_sqft = (
            float(obj.price) / float(obj.numeric_area)
            if obj.price and obj.numeric_area
            else None
        )

        avg_price = "—"
        pf_avg_roi = None
        avg_exposure_days = None
        area_avg_days = obj.area.avg_days_on_market if obj.area else None

        if obj.area:
            area_avg_days_on_market = obj.area.avg_days_on_market

        if obj.building:
            bld = obj.building
            # Bld exposure
            if list_type == "sale":
                n_ads, exp_sum = (
                    bld.numbers_of_processed_sale_ads,
                    bld.sum_exposure_sale_days,
                )
            else:
                n_ads, exp_sum = (
                    bld.numbers_of_processed_rent_ads,
                    bld.sum_exposure_rent_days,
                )
            avg_exposure_days = round(exp_sum / n_ads, 2) if n_ads else None

            def _avg(attr):
                return float(getattr(bld, attr, 0) or 0.0)

            bed = obj.bedrooms or ""
            if list_type == "sale":
                pf_avg_roi = {
                    "studio": lambda: _avg("avg_rent_studio") / float(obj.price)
                    if obj.price
                    else None,
                    "1": lambda: _avg("avg_rent_1br") / float(obj.price)
                    if obj.price
                    else None,
                    "2": lambda: _avg("avg_rent_2br") / float(obj.price)
                    if obj.price
                    else None,
                    "3": lambda: _avg("avg_rent_3br") / float(obj.price)
                    if obj.price
                    else None,
                    "4": lambda: _avg("avg_rent_4br") / float(obj.price)
                    if obj.price
                    else None,
                }.get(
                    bed,
                    lambda: _avg("avg_rent_4br") / float(obj.price)
                    if obj.price
                    else None,
                )()
                avg_price = {
                    "studio": _avg("avg_sale_studio"),
                    "1": _avg("avg_sale_1br"),
                    "2": _avg("avg_sale_2br"),
                    "3": _avg("avg_sale_3br"),
                    "4": _avg("avg_sale_4br"),
                }.get(bed, _avg("avg_sale_4br"))
                avg_price = f"{avg_price:.2f} AED"

                pf_avg_roi_rent = {
                    "studio": lambda: _avg("avg_rent_studio") / _avg("avg_sale_studio")
                    if _avg("avg_sale_studio")
                    else None,
                    "1": lambda: _avg("avg_rent_1br") / _avg("avg_sale_1br")
                    if _avg("avg_sale_1br")
                    else None,
                    "2": lambda: _avg("avg_rent_2br") / _avg("avg_sale_2br")
                    if _avg("avg_sale_2br")
                    else None,
                    "3": lambda: _avg("avg_rent_3br") / _avg("avg_sale_3br")
                    if _avg("avg_sale_3br")
                    else None,
                    "4": lambda: _avg("avg_rent_4br") / _avg("avg_sale_4br")
                    if _avg("avg_sale_4br")
                    else None,
                }.get(
                    bed,
                    lambda: _avg("avg_rent_4br") / _avg("avg_sale_4br")
                    if _avg("avg_sale_4br")
                    else None,
                )()

                avg_price_rent = {
                    "studio": _avg("avg_rent_studio"),
                    "1": _avg("avg_rent_1br"),
                    "2": _avg("avg_rent_2br"),
                    "3": _avg("avg_rent_3br"),
                    "4": _avg("avg_rent_4br"),
                }.get(bed, _avg("avg_rent_4br"))

            else:
                pf_avg_roi = {
                    "studio": lambda: _avg("avg_rent_studio") / _avg("avg_sale_studio")
                    if _avg("avg_sale_studio")
                    else None,
                    "1": lambda: _avg("avg_rent_1br") / _avg("avg_sale_1br")
                    if _avg("avg_sale_1br")
                    else None,
                    "2": lambda: _avg("avg_rent_2br") / _avg("avg_sale_2br")
                    if _avg("avg_sale_2br")
                    else None,
                    "3": lambda: _avg("avg_rent_3br") / _avg("avg_sale_3br")
                    if _avg("avg_sale_3br")
                    else None,
                    "4": lambda: _avg("avg_rent_4br") / _avg("avg_sale_4br")
                    if _avg("avg_sale_4br")
                    else None,
                }.get(
                    bed,
                    lambda: _avg("avg_rent_4br") / _avg("avg_sale_4br")
                    if _avg("avg_sale_4br")
                    else None,
                )()
                avg_price = {
                    "studio": _avg("avg_rent_studio"),
                    "1": _avg("avg_rent_1br"),
                    "2": _avg("avg_rent_2br"),
                    "3": _avg("avg_rent_3br"),
                    "4": _avg("avg_rent_4br"),
                }.get(bed, _avg("avg_rent_4br"))
                avg_price = f"{avg_price:.2f} AED"

                pf_avg_roi_rent = pf_avg_roi
                avg_price_rent = avg_price
            numbers_of_processed_sale_ads_with_same_rooms = {
                "studio": _avg("sale_count_studio"),
                "1": _avg("sale_count_1br"),
                "2": _avg("sale_count_1br"),
                "3": _avg("sale_count_1br"),
                "4": _avg("sale_count_1br"),
            }.get(bed, _avg("avg_rent_4br"))

        raw_list.append(
            {
                "obj": obj,
                "days_on_market": days_on_market,
                "area_avg_days": area_avg_days,
                "price_per_sqft": price_per_sqft,
                "pf_avg_roi": pf_avg_roi,
                "avg_exposure_days": avg_exposure_days,
                "avg_price": avg_price,
                "area_avg_days_on_market": area_avg_days_on_market,
                "pf_avg_roi_rent": pf_avg_roi_rent,
                "avg_price_rent": avg_price_rent,
                "numbers_of_processed_sale_ads_with_same_rooms": numbers_of_processed_sale_ads_with_same_rooms,
            }
        )
    #
    # # фильтрация по ROI
    # pf_min = float(pf_roi_min_str) if pf_roi_min_str else None
    # pf_max = float(pf_roi_max_str) if pf_roi_max_str else None
    #
    # if pf_min is not None:
    #     raw_list = [r for r in raw_list if (r["pf_avg_roi"] or 0) >= pf_min]
    # if pf_max is not None:
    #     raw_list = [r for r in raw_list if (r["pf_avg_roi"] or 0) <= pf_max]
    price_min = float(price_min_str) if price_min_str else None
    price_max = float(price_max_str) if price_max_str else None
    if price_min is not None:
        raw_list = [r for r in raw_list if (r["obj"].price or 0) >= price_min]
    if price_max is not None:
        raw_list = [r for r in raw_list if (r["obj"].price or 0) <= price_max]
    # сортировка
    reverse = sort_order == "desc"

    def keyfunc(item):
        if sort_field == "days":
            return item["days_on_market"] or 9e9
        if sort_field == "price_sqft":
            return item["price_per_sqft"] or 0
        if sort_field == "roi":
            return item["pf_avg_roi"] or 0
        return item["obj"].id

    raw_list.sort(key=keyfunc, reverse=reverse)

    page_obj = Paginator(raw_list, 10).get_page(page_number)

    all_areas = (
        Area.objects.filter(verified_value__isnull=False)
        .exclude(verified_value__exact="")
        .order_by("name")
    )

    context = {
        "page_obj": page_obj,
        "search_query": q,
        "filter_area": filter_area,
        # "pf_avg_roi_min": pf_roi_min_str,
        # "pf_avg_roi_max": pf_roi_max_str,
        "price_min": price_min_str,
        "price_max": price_max_str,
        "sort_field": sort_field,
        "sort_order": sort_order,
        "all_areas": all_areas,
        "list_type": list_type,
    }
    return context, page_obj

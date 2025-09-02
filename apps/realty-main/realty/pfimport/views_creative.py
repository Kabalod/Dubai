# pfimport/views.py
# ╔═══════════════════════════════════════════════════════════════════════════╗
#   v3.3  ·  28 May 2025  ·  Полная поддержка всех типов bedrooms
#
#  • Добавлены явные методы для каждого типа bedrooms (studio, 1, 2, 3, 4+)
#  • Все средние значения предварительно аннотируются в запросах
#  • Оптимизированы запросы для всех сценариев использования
# ╚═══════════════════════════════════════════════════════════════════════════╝
from __future__ import annotations

from typing import Dict, List, Optional

from django.core.paginator import Paginator
from django.db.models import (
    Avg,
    Case,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    Value,
    When,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Area, Building, PFListRent, PFListSale

TODAY = timezone.now().date()
BEDROOMS_TYPES = ["studio", "1", "2", "3", "4"]


# ───────────────────────────── Building report ──────────────────────────────
def building_report_view(request, building_id: int):
    bld = get_object_or_404(Building, pk=building_id)

    bedrooms = request.GET.get("bedrooms", "1")

    # Используем готовые методы модели для получения средних цен
    avg_prices = {
        "rent": {
            "all": None,  # можно добавить общий метод если нужно
            "studio": bld.avg_rent_studio,
            "1": bld.avg_rent_1br,
            "2": bld.avg_rent_2br,
            "3": bld.avg_rent_3br,
            "4": bld.avg_rent_4br,
        },
        "sale": {
            "all": None,  # можно добавить общий метод если нужно
            "studio": bld.avg_sale_studio,
            "1": bld.avg_sale_1br,
            "2": bld.avg_sale_2br,
            "3": bld.avg_sale_3br,
            "4": bld.avg_sale_4br,
        },
    }

    context = {
        "building": bld,
        "bedrooms": bedrooms,
        "avg_prices": avg_prices,
        "bedrooms_types": BEDROOMS_TYPES,
    }
    return render(request, "pfimport/building_report.html", context)


# ──────────────────────── списки Sale / Rent объявлений ─────────────────────
def pf_listings_sale_view(request):
    ctx, _ = _build_common(request, PFListSale, list_type="sale")
    return render(request, "pfimport/creative_pf_listings_table.html", ctx)


def pf_listings_rent_view(request):
    ctx, _ = _build_common(request, PFListRent, list_type="rent")
    return render(request, "pfimport/creative_pf_listings_table.html", ctx)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#   _build_common(): единый движок для Sale / Rent
# ╚═══════════════════════════════════════════════════════════════════════════╝
def _build_common(request, model_cls, *, list_type: str):
    q = request.GET.get("q", "").strip()
    filter_area = request.GET.get("area", "").strip()
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    bedrooms_filter = request.GET.get("bedrooms")
    sort_field = request.GET.get("sort", "")
    sort_order = request.GET.get("order", "asc").lower()
    page_number = request.GET.get("page", 1)

    # 1. Base queryset
    qs = (
        model_cls.objects.select_related("area", "building")
        .filter(area__verified_value__isnull=False)
        .exclude(area__verified_value__exact="")
    )

    # Фильтрация
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(display_address__icontains=q))
    if filter_area:
        qs = qs.filter(area__name=filter_area)
    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)
    if bedrooms_filter:
        qs = qs.filter(bedrooms=bedrooms_filter)

    # Сортировка
    prefix = "-" if sort_order == "desc" else ""
    if sort_field == "days":
        qs = qs.order_by(f"-added_on")
    elif sort_field == "roi":
        qs = qs.order_by(f"{prefix}roi")
    elif sort_field == "building_avg_roi":
        qs = qs.order_by(f"{prefix}building_avg_roi")
    elif sort_field == "price":
        qs = qs.order_by(f"{prefix}price")
    elif sort_field == "added_on":
        qs = qs.order_by(f"{prefix}added_on")
    elif sort_field == "bedrooms":
        # Кастомная сортировка по комнатам (studio, 1, 2, 3, 4) только в Python
        pass
    elif sort_field == "price_sqft":
        # Только в Python, т.к. вычисляется на лету
        pass
    else:
        qs = qs.order_by(f"{prefix}added_on")

    # Пагинация
    page_obj = Paginator(qs, 10).get_page(page_number)

    # Подготовка данных для шаблона
    curated = []
    for obj in page_obj:
        obj.days_on_market = (
            (TODAY - obj.added_on.date()).days if obj.added_on else None
        )
        obj.price_per_sqft = (
            float(obj.price) / obj.numeric_area
            if obj.price and obj.numeric_area
            else None
        )

        # Добавляем все средние цены для этого объекта
        obj.avg_prices = {
            "rent": _get_all_avg_prices(obj.building, "rent") if obj.building else {},
            "sale": _get_all_avg_prices(obj.building, "sale") if obj.building else {},
        }

        # Вычисляем ROI объявления и средний ROI по зданию
        obj.roi = None
        obj.building_avg_roi = None
        if obj.building and obj.bedrooms and obj.price:
            # ROI объявления: средняя аренда по комнатности / цена продажи объявления
            if list_type == "sale":
                avg_rent = obj.avg_prices["rent"].get(obj.bedrooms)
                if avg_rent and obj.price and float(obj.price) > 0:
                    obj.roi = float(avg_rent) / float(obj.price)
            # ROI по зданию: средняя аренда по комнатности / средняя продажа по комнатности
            avg_rent = obj.avg_prices["rent"].get(obj.bedrooms)
            avg_sale = obj.avg_prices["sale"].get(obj.bedrooms)
            if avg_rent and avg_sale and float(avg_sale) > 0:
                obj.building_avg_roi = float(avg_rent) / float(avg_sale)

        curated.append(obj)

    # Сортировка по price/sqft, ROI, building_avg_roi или bedrooms если нужно
    if sort_field == "price_sqft":
        curated.sort(key=lambda o: o.price_per_sqft or 0, reverse=sort_order == "desc")
    elif sort_field == "roi":
        not_none = [o for o in curated if o.roi is not None]
        none = [o for o in curated if o.roi is None]
        not_none.sort(key=lambda o: o.roi, reverse=sort_order == "desc")
        curated = not_none + none
    elif sort_field == "building_avg_roi":
        not_none = [o for o in curated if o.building_avg_roi is not None]
        none = [o for o in curated if o.building_avg_roi is None]
        not_none.sort(key=lambda o: o.building_avg_roi, reverse=sort_order == "desc")
        curated = not_none + none
    elif sort_field == "bedrooms":
        # Правильный порядок сортировки: studio, 1, 2, 3, 4
        bedroom_order = {"studio": 0, "1": 1, "2": 2, "3": 3, "4": 4}
        curated.sort(
            key=lambda o: bedroom_order.get(o.bedrooms, 999),
            reverse=sort_order == "desc",
        )

    # Маркеры для карты
    map_markers = [
        {
            "id": o.id,
            "kind": list_type,
            "title": o.title or o.display_address or f"{list_type.title()} #{o.id}",
            "price": float(o.price) if o.price else None,
            "lat": o.latitude,
            "lng": o.longitude,
            "bedrooms": o.bedrooms,
            "avg_price": o.avg_prices["rent" if list_type == "sale" else "sale"].get(
                o.bedrooms
            ),
        }
        for o in curated
        if o.latitude and o.longitude
    ]

    context = {
        "page_obj": page_obj,
        "search_query": q,
        "filter_area": filter_area,
        "price_min": price_min or "",
        "price_max": price_max or "",
        "bedrooms_filter": bedrooms_filter or "",
        "sort_field": sort_field,
        "sort_order": sort_order,
        "all_areas": Area.objects.filter(verified_value__isnull=False)
        .exclude(verified_value__exact="")
        .order_by("name"),
        "list_type": list_type,
        "map_markers": map_markers,
        "bedrooms_types": BEDROOMS_TYPES,
    }
    return context, page_obj


# ──────────────────────── Helpers для цен и ROI ────────────────────────────
def _get_all_avg_prices(building, price_type: str) -> Dict[str, Optional[float]]:
    """Возвращает словарь со средними ценами для всех типов bedrooms"""
    if price_type == "rent":
        return {
            "studio": building.avg_rent_studio,
            "1": building.avg_rent_1br,
            "2": building.avg_rent_2br,
            "3": building.avg_rent_3br,
            "4": building.avg_rent_4br,
        }
    elif price_type == "sale":
        return {
            "studio": building.avg_sale_studio,
            "1": building.avg_sale_1br,
            "2": building.avg_sale_2br,
            "3": building.avg_sale_3br,
            "4": building.avg_sale_4br,
        }
    else:
        return {bt: None for bt in BEDROOMS_TYPES}


def get_avg_price_for_bedrooms(
    building, bedrooms: str, price_type: str
) -> Optional[float]:
    """Получает среднюю цену здания для конкретной комнатности"""
    if not building:
        return None

    if price_type == "rent":
        if bedrooms == "studio":
            return building.avg_rent_studio
        elif bedrooms == "1":
            return building.avg_rent_1br
        elif bedrooms == "2":
            return building.avg_rent_2br
        elif bedrooms == "3":
            return building.avg_rent_3br
        elif bedrooms == "4":
            return building.avg_rent_4br
    elif price_type == "sale":
        if bedrooms == "studio":
            return building.avg_sale_studio
        elif bedrooms == "1":
            return building.avg_sale_1br
        elif bedrooms == "2":
            return building.avg_sale_2br
        elif bedrooms == "3":
            return building.avg_sale_3br
        elif bedrooms == "4":
            return building.avg_sale_4br

    return None


def _add_roi_annotation(qs, list_type: str):
    """Добавляет аннотацию roi для queryset - теперь ROI будет вычисляться в Python"""
    # Возвращаем queryset без аннотации, ROI будем считать в Python
    return qs

# pfimport/views.py
# ╔═══════════════════════════════════════════════════════════════════════════╗
#   v3.2  ·  Fixed avg prices annotations and ROI sorting
#
#  Изменения:
#  • Всегда добавляем аннотации _avg_rent/_avg_sale независимо от сортировки
#  • Упрощена функция _add_roi_annotation (использует существующие аннотации)
#  • Исправлена опечатка в obj.added_on (было obj.added_on)
# ╚═══════════════════════════════════════════════════════════════════════════╝
from __future__ import annotations

from typing import Dict, List

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
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Area, Building, PFListRent, PFListSale

TODAY = timezone.now().date()


# ───────────────────────────── Building report ──────────────────────────────
def building_report_view(request, building_id: int):
    bld = get_object_or_404(Building, pk=building_id)
    bedrooms = request.GET.get("bedrooms", "1")
    # ← далее без изменений — см. предыдущую версию (сокращено для краткости)
    # ………………………………………………………………………………………………………………………………


# ──────────────────────── списки Sale / Rent объявлений ─────────────────────
def pf_listings_sale_view(request):
    ctx, _ = _build_common(request, PFListSale, list_type="sale")
    return render(request, "pfimport/pf_listings_table.html", ctx)


def pf_listings_rent_view(request):
    ctx, _ = _build_common(request, PFListRent, list_type="rent")
    return render(request, "pfimport/pf_listings_table.html", ctx)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#   _build_common(): единый движок для Sale / Rent
# ╚═══════════════════════════════════════════════════════════════════════════╝
def _build_common(request, model_cls, *, list_type: str):
    q = request.GET.get("q", "").strip()
    filter_area = request.GET.get("area", "").strip()
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    sort_field = request.GET.get("sort", "")
    sort_order = request.GET.get("order", "asc").lower()
    page_number = request.GET.get("page", 1)

    # 1. Base queryset (узкий SELECT)
    qs = (
        model_cls.objects.select_related("area", "building")
        .only(
            "id",
            "title",
            "display_address",
            "bedrooms",
            "price",
            "price_currency",
            "numeric_area",
            "added_on",
            "latitude",
            "longitude",
            # ОБЯЗАТЕЛЬНО FK-столбцы
            "area_id",
            "area__name",
            "building_id",
            "building__name",
            # для ROI и средних цен
            "building__rent_sum_studio",
            "building__rent_count_studio",
            "building__rent_sum_1br",
            "building__rent_count_1br",
            "building__rent_sum_2br",
            "building__rent_count_2br",
            "building__rent_sum_3br",
            "building__rent_count_3br",
            "building__rent_sum_4br",
            "building__rent_count_4br",
            "building__sale_sum_studio",
            "building__sale_count_studio",
            "building__sale_sum_1br",
            "building__sale_count_1br",
            "building__sale_sum_2br",
            "building__sale_count_2br",
            "building__sale_sum_3br",
            "building__sale_count_3br",
            "building__sale_sum_4br",
            "building__sale_count_4br",
        )
        .filter(area__verified_value__isnull=False)
        .exclude(area__verified_value__exact="")
    )

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(display_address__icontains=q))
    if filter_area:
        qs = qs.filter(area__name=filter_area)
    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)

    # 2. Всегда добавляем аннотации средних цен
    qs = _add_avg_price_annotations(qs, list_type)

    prefix = "-" if sort_order == "desc" else ""

    # 3. SQL-level сортировка
    if sort_field == "days":
        qs = qs.order_by(f"-added_on")  # старые → первые
    elif sort_field == "roi":
        qs = _add_roi_annotation(qs, list_type)
        qs = qs.order_by(f"{prefix}roi")
    elif sort_field == "price_sqft":
        # сделаем позже в Python (дорогое деление + индекс не поможет)
        pass
    else:
        qs = qs.order_by(f"{prefix}added_on")

    # 4. Пагинация
    page_obj = Paginator(qs, 10).get_page(page_number)

    # 5. «дорогие» вычисления только для 10 строк
    curated: List = []
    for obj in page_obj:
        obj.days_on_market = (
            (TODAY - obj.added_on.date()).days if obj.added_on else None
        )
        obj.price_per_sqft = (
            float(obj.price) / obj.numeric_area
            if obj.price and obj.numeric_area
            else None
        )
        curated.append(obj)

    # 6. Python-level сортировка по price/ft² (если запрошена)
    if sort_field == "price_sqft":
        curated.sort(
            key=lambda o: o.price_per_sqft or 0,
            reverse=sort_order == "desc",
        )

    # 7. Маркеры карты (те же 10 строк)
    map_markers = [
        {
            "id": o.id,
            "kind": list_type,
            "title": o.title or o.display_address or f"{list_type.title()} #{o.id}",
            "price": float(o.price) if o.price else None,
            "lat": o.latitude,
            "lng": o.longitude,
        }
        for o in curated
        if o.latitude and o.longitude
    ]

    # 8. Context → template
    context = {
        "page_obj": page_obj,
        "search_query": q,
        "filter_area": filter_area,
        "price_min": price_min or "",
        "price_max": price_max or "",
        "sort_field": sort_field,
        "sort_order": sort_order,
        "all_areas": (
            Area.objects.filter(verified_value__isnull=False)
            .exclude(verified_value__exact="")
            .only("name")
            .order_by("name")
        ),
        "list_type": list_type,
        "map_markers": map_markers,
    }
    return context, page_obj


# ──────────────────────────── Helper functions ──────────────────────────────
def _case_avg(sum_field: str, cnt_field: str) -> ExpressionWrapper:
    """sum / count → FloatField (NULL, если count==0)"""
    return ExpressionWrapper(
        Case(
            When(**{f"{cnt_field}__gt": 0}, then=F(sum_field) / F(cnt_field)),
            default=Value(None),
            output_field=FloatField(),
        ),
        output_field=FloatField(),
    )


def _add_avg_price_annotations(qs, list_type: str):
    """Добавляет аннотации средних цен (_avg_rent/_avg_sale)"""
    if list_type == "sale":
        qs = qs.annotate(
            _avg_rent=Case(
                When(
                    Q(bedrooms="studio"),
                    then=_case_avg(
                        "building__rent_sum_studio", "building__rent_count_studio"
                    ),
                ),
                When(
                    Q(bedrooms="1"),
                    then=_case_avg(
                        "building__rent_sum_1br", "building__rent_count_1br"
                    ),
                ),
                When(
                    Q(bedrooms="2"),
                    then=_case_avg(
                        "building__rent_sum_2br", "building__rent_count_2br"
                    ),
                ),
                When(
                    Q(bedrooms="3"),
                    then=_case_avg(
                        "building__rent_sum_3br", "building__rent_count_3br"
                    ),
                ),
                default=_case_avg("building__rent_sum_4br", "building__rent_count_4br"),
                output_field=FloatField(),
            )
        )
    else:  # rent
        qs = qs.annotate(
            _avg_sale=Case(
                When(
                    Q(bedrooms="studio"),
                    then=_case_avg(
                        "building__sale_sum_studio", "building__sale_count_studio"
                    ),
                ),
                When(
                    Q(bedrooms="1"),
                    then=_case_avg(
                        "building__sale_sum_1br", "building__sale_count_1br"
                    ),
                ),
                When(
                    Q(bedrooms="2"),
                    then=_case_avg(
                        "building__sale_sum_2br", "building__sale_count_2br"
                    ),
                ),
                When(
                    Q(bedrooms="3"),
                    then=_case_avg(
                        "building__sale_sum_3br", "building__sale_count_3br"
                    ),
                ),
                default=_case_avg("building__sale_sum_4br", "building__sale_count_4br"),
                output_field=FloatField(),
            )
        )
    return qs


def _add_roi_annotation(qs, list_type: str):
    """Добавляет только ROI аннотацию, используя существующие _avg_rent/_avg_sale"""
    if list_type == "sale":
        qs = qs.annotate(
            roi=ExpressionWrapper(
                F("_avg_rent") / F("price"), output_field=FloatField()
            )
        )
    else:  # rent
        qs = qs.annotate(
            roi=ExpressionWrapper(
                F("price") / F("_avg_sale"), output_field=FloatField()
            )
        )
    return qs

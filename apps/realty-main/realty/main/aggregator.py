from typing import Optional

from django.db.models import Avg
from django.db.models import Count
from django.db.models import Max
from django.db.models import Min
from django.db.models import Sum

from .models import Building
from .models import MergedTransaction


def _calc_percent_change(
    current_value: Optional[float], previous_value: Optional[float]
) -> float:
    """
    Процентное изменение = ((current - previous) / previous) * 100,
    если previous=0 или None => 0.0.
    """
    if not previous_value or previous_value == 0:
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100.0


def _approximate_median_via_minmax(min_val, max_val):
    """
    Приближённая медиана как (min_val + max_val) / 2,
    если оба значения не None.
    """
    if min_val is not None and max_val is not None:
        return (min_val + max_val) / 2.0
    return None


def _aggregator_for_qs(qs):
    """
    Считает агрегаты по одному QuerySet (все сделки за период).
    Возвращает словарь с:
      - deals_count
      - buildings_count
      - avg_price
      - min_price
      - max_price
      - sum_price
      - sum_sqm
      - avg_roi
      - median_price (по min+max, приблизительно)
      - avg_price_sqm (sum_price / sum_sqm)
    При извлечении значений из агрегаций приводим Decimal → float.
    """
    agg = qs.aggregate(
        deals_count=Count("*"),
        buildings_count=Count("building", distinct=True),
        avg_price=Avg("transaction_price"),
        min_price=Min("transaction_price"),
        max_price=Max("transaction_price"),
        sum_price=Sum("transaction_price"),
        sum_sqm=Sum("sqm"),
        avg_roi=Avg("roi"),
    )
    avg_price = float(agg["avg_price"]) if agg["avg_price"] is not None else 0.0
    min_price = float(agg["min_price"]) if agg["min_price"] is not None else 0.0
    max_price = float(agg["max_price"]) if agg["max_price"] is not None else 0.0
    sum_price = float(agg["sum_price"] or 0.0)
    sum_sqm = float(agg["sum_sqm"] or 0.0)
    avg_roi = float(agg["avg_roi"]) if agg["avg_roi"] is not None else 0.0

    median_price_approx = _approximate_median_via_minmax(min_price, max_price)
    avg_price_sqm = sum_price / sum_sqm if sum_sqm > 0 else 0.0

    return {
        "deals_count": agg["deals_count"],
        "buildings_count": agg["buildings_count"],
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "sum_price": sum_price,
        "sum_sqm": sum_sqm,
        "avg_roi": avg_roi,
        "median_price": median_price_approx if median_price_approx is not None else 0.0,
        "avg_price_sqm": avg_price_sqm,
    }


def aggregator_2periods(qs_current, qs_previous, transaction_type: str):
    """
    Если transaction_type == 'rental':
        - ничего не считаем, сразу отдаём хардкодный словарь.
    Иначе считаем все метрики для 'sales' (или другого transaction_type, кроме 'rental').

    Принимает два QuerySet:
      1) qs_current – сделки за текущий период (обычно transaction_type='sales'),
      2) qs_previous – сделки за предыдущий период (тот же тип).

    Возвращает словарь с метриками.
    """
    # Если это аренда - возвращаем хардкод
    if transaction_type == "rental":
        return {
            "total_buildings": 0,
            "total_deals": 0,
            "total_properties": 0,
            "growth_dynamic_percent": 0.0,
            "averagePrice_value": 0.0,
            "averagePrice_dynamic": 0.0,
            "averagePrice_range": "[0, 0]",
            "averagePrice_versus": 0.0,
            "averagePrice_comparison": 0.0,
            "medianPrice_value": 0.0,
            "medianPrice_dynamic": 0.0,
            "medianPrice_range": "",
            "medianPrice_versus": 0.0,
            "medianPrice_comparison": 0.0,
            "averagePricePerSQM_value": 0.0,
            "averagePricePerSQM_dynamic": 0.0,
            "averagePricePerSQM_range": "",
            "averagePricePerSQM_versus": 0.0,
            "averagePricePerSQM_comparison": 0.0,
            "priceRange_value": 0.0,
            "priceRange_dynamic": 0.0,
            "priceRange_range": "[0, 0]",
            "priceRange_versus": 0.0,
            "priceRange_comparison": 0.0,
            "deals_value": 0.0,
            "deals_dynamic": 0.0,
            "deals_range": "",
            "deals_versus": 0.0,
            "deals_comparison": 0.0,
            "dealsVolume_value": 0.0,
            "dealsVolume_dynamic": 0.0,
            "dealsVolume_range": "",
            "dealsVolume_versus": 0.0,
            "dealsVolume_comparison": 0.0,
            "liquidity_value": 0.0,
            "liquidity_dynamic": 0.0,
            "liquidity_range": "",
            "liquidity_versus": 0.0,
            "liquidity_comparison": 0.0,
            "roi_value": 0.0,
            "roi_dynamic": 0.0,
            "roi_range": "",
            "roi_versus": 0.0,
            "roi_comparison": 0.0,
        }

    # --- Ниже всё для продаж (или другого типа, кроме 'rental'). ---
    curr = _aggregator_for_qs(qs_current)
    prev = _aggregator_for_qs(qs_previous)

    # Определяем period
    if qs_current.exists():
        first_tx = qs_current.first()
        period = first_tx.period or str(first_tx.date_of_transaction.year)
    else:
        period = None

    # Если получили period, пытаемся взять все сделки с этим же period, иначе все
    if period:
        all_deals_qs = MergedTransaction.objects.filter(period=period)
        if not all_deals_qs.exists():
            # Если period не сработал, пробуем deal_year
            try:
                all_deals_qs = MergedTransaction.objects.filter(deal_year=int(period))
            except ValueError:
                all_deals_qs = MergedTransaction.objects.all()
    else:
        all_deals_qs = MergedTransaction.objects.all()

    all_metrics = _aggregator_for_qs(all_deals_qs)

    # Считаем total_buildings (уникальные здания в qs_current)
    building_ids_current = qs_current.values_list("building_id", flat=True).distinct()
    buildings_in_current = Building.objects.filter(id__in=building_ids_current)
    total_buildings = buildings_in_current.count()

    # total_deals
    total_deals = curr["deals_count"]

    # total_properties
    total_properties = 0
    for b in buildings_in_current:
        if b.total_units and b.total_units > 0:
            total_properties += b.total_units
        else:
            total_properties += 1

    # growth_dynamic_percent = процент изменения total_deals
    growth_dynamic_percent = _calc_percent_change(total_deals, prev["deals_count"])

    # averagePrice
    average_price_value = curr["avg_price"]
    average_price_dynamic = _calc_percent_change(curr["avg_price"], prev["avg_price"])
    average_price_range_str = f"[{curr['min_price']}, {curr['max_price']}]"
    average_price_versus = _calc_percent_change(
        average_price_value, all_metrics["avg_price"]
    )

    # Сравнение со сделками по другим area (не входящим в qs_current)
    if period and qs_current.exists():
        current_area_ids = (
            qs_current.values_list("area_id", flat=True)
            .exclude(area_id__isnull=True)
            .distinct()
        )
        deals_excl_areas = all_deals_qs.exclude(area_id__in=current_area_ids)
        excl_metrics = _aggregator_for_qs(deals_excl_areas)
        average_price_comparison = _calc_percent_change(
            average_price_value, excl_metrics["avg_price"]
        )
    else:
        average_price_comparison = 0.0

    # medianPrice
    median_price_value = curr["median_price"]
    median_price_dynamic = _calc_percent_change(
        curr["median_price"], prev["median_price"]
    )
    median_price_versus = _calc_percent_change(
        median_price_value, all_metrics["median_price"]
    )
    median_price_comparison = median_price_dynamic

    # averagePricePerSQM
    avg_ps_value = curr["avg_price_sqm"]
    avg_ps_dynamic = _calc_percent_change(curr["avg_price_sqm"], prev["avg_price_sqm"])
    avg_ps_versus = _calc_percent_change(avg_ps_value, all_metrics["avg_price_sqm"])
    avg_ps_comparison = avg_ps_dynamic

    # priceRange
    price_range_value = curr["max_price"] - curr["min_price"]
    price_range_str = f"[{curr['min_price']}, {curr['max_price']}]"

    def midpoint(a, b):
        return (a + b) / 2.0 if a and b else 0.0

    curr_mid = midpoint(curr["min_price"], curr["max_price"])
    prev_mid = midpoint(prev["min_price"], prev["max_price"])
    all_mid = midpoint(all_metrics["min_price"], all_metrics["max_price"])
    price_range_dynamic = _calc_percent_change(curr_mid, prev_mid)
    price_range_versus = _calc_percent_change(curr_mid, all_mid)
    price_range_comparison = price_range_dynamic

    # deals
    deals_value = float(total_deals)
    deals_dynamic = _calc_percent_change(deals_value, float(prev["deals_count"]))
    deals_versus = _calc_percent_change(deals_value, float(all_metrics["deals_count"]))
    deals_comparison = deals_dynamic

    # dealsVolume
    dealsVolume_value = curr["sum_price"]
    dealsVolume_dynamic = _calc_percent_change(dealsVolume_value, prev["sum_price"])
    dealsVolume_versus = _calc_percent_change(
        dealsVolume_value, all_metrics["sum_price"]
    )
    dealsVolume_comparison = dealsVolume_dynamic

    # liquidity (примем за proxy – avg_price_sqm)
    liquidity_value = avg_ps_value
    liquidity_dynamic = avg_ps_dynamic
    liquidity_versus = _calc_percent_change(
        liquidity_value, all_metrics["avg_price_sqm"]
    )
    liquidity_comparison = liquidity_dynamic

    # roi
    roi_value = curr["avg_roi"]
    roi_dynamic = _calc_percent_change(curr["avg_roi"], prev["avg_roi"])
    roi_versus = _calc_percent_change(roi_value, all_metrics["avg_roi"])
    roi_comparison = roi_dynamic

    return {
        "total_buildings": total_buildings,
        "total_deals": total_deals,
        "total_properties": total_properties,
        "growth_dynamic_percent": growth_dynamic_percent,
        "averagePrice_value": average_price_value,
        "averagePrice_dynamic": average_price_dynamic,
        "averagePrice_range": average_price_range_str,
        "averagePrice_versus": average_price_versus,
        "averagePrice_comparison": average_price_comparison,
        "medianPrice_value": median_price_value,
        "medianPrice_dynamic": median_price_dynamic,
        "medianPrice_range": "",
        "medianPrice_versus": median_price_versus,
        "medianPrice_comparison": median_price_comparison,
        "averagePricePerSQM_value": avg_ps_value,
        "averagePricePerSQM_dynamic": avg_ps_dynamic,
        "averagePricePerSQM_range": "",
        "averagePricePerSQM_versus": avg_ps_versus,
        "averagePricePerSQM_comparison": avg_ps_comparison,
        "priceRange_value": price_range_value,
        "priceRange_dynamic": price_range_dynamic,
        "priceRange_range": price_range_str,
        "priceRange_versus": price_range_versus,
        "priceRange_comparison": price_range_comparison,
        "deals_value": deals_value,
        "deals_dynamic": deals_dynamic,
        "deals_range": "",
        "deals_versus": deals_versus,
        "deals_comparison": deals_comparison,
        "dealsVolume_value": dealsVolume_value,
        "dealsVolume_dynamic": dealsVolume_dynamic,
        "dealsVolume_range": "",
        "dealsVolume_versus": dealsVolume_versus,
        "dealsVolume_comparison": dealsVolume_comparison,
        "liquidity_value": liquidity_value,
        "liquidity_dynamic": liquidity_dynamic,
        "liquidity_range": "",
        "liquidity_versus": liquidity_versus,
        "liquidity_comparison": liquidity_comparison,
        "roi_value": roi_value,
        "roi_dynamic": roi_dynamic,
        "roi_range": "",
        "roi_versus": roi_versus,
        "roi_comparison": roi_comparison,
    }

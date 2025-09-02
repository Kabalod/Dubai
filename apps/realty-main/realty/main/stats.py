import hashlib
import json
import statistics
from collections import defaultdict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

from django.core.cache import cache
from django.db.models import Q

from .models import Area
from .models import Building
from .models import BuildingLiquidityParameterOne
from .models import Project
from .models import SearchTransactionsLog
from .utils import _build_transactions_queryset
from .utils import _get_period_range


def calculate_total_units_sum(buildings: Iterable[Building]) -> float:
    """
    Calculates the total units sum over a collection of buildings.

    For each building:
      - If building.total_units is provided and > 0, it is used.
      - Otherwise, the building's project's total_units is used.
    """
    total = 0.0
    for building in buildings:
        if building.total_units and building.total_units > 0:
            total += building.total_units
        elif building.project and building.project.total_units:
            total += building.project.total_units
    return total


def compute_total_buildings(search_substring: Optional[str]) -> Dict[str, float]:
    """
    Computes the total number of buildings and the total units sum based on the search substring:

    1. If an Area is found via the search substring (matching name_en or name_ar),
       returns a dictionary with:
         - "building_count": count of buildings in those areas.
         - "units_sum": total units sum for those buildings.
    2. Otherwise, if Buildings with names matching the search substring exist,
       returns a dictionary with:
         - "building_count": count of those buildings.
         - "units_sum": total units sum for those buildings.
    3. If neither is found, returns a dictionary with:
         - "building_count": count of all projects (?). Or sum of all buildings.
         - "units_sum": total units sum for all projects.
    """

    # if search_substring and search_substring.strip():
    #     search_str = search_substring.strip()
    #     area_qs = Area.objects.filter(
    #         Q(name_en__icontains=search_str) | Q(name_ar__icontains=search_str)
    #     )
    #     if area_qs.exists():
    #         building_qs = Building.objects.filter(area__in=area_qs)
    #         building_count = building_qs.count()
    #         units_sum = calculate_total_units_sum(building_qs)
    #         return {"building_count": building_count, "units_sum": units_sum}
    #     else:
    #         building_qs = Building.objects.filter(english_name__icontains=search_str)
    #         if building_qs.exists():
    #             building_count = building_qs.count()
    #             units_sum = calculate_total_units_sum(building_qs)
    #             return {"building_count": building_count, "units_sum": units_sum}
    #         else:
    #             project_qs = Project.objects.all()
    #             building_count = project_qs.count()
    #             units_sum = sum(p.total_units or 0 for p in project_qs)
    #             return {"building_count": building_count, "units_sum": units_sum}
    # else:
    #     project_qs = Project.objects.all()
    #     building_count = project_qs.count()
    #     units_sum = sum(p.total_units or 0 for p in project_qs)
    #     return {"building_count": building_count, "units_sum": units_sum}
    if search_substring and search_substring.strip():
        search_str = search_substring.strip()
        area_qs = Area.objects.filter(
            Q(name_en__icontains=search_str) | Q(name_ar__icontains=search_str)
        )
        if area_qs.exists():
            building_qs = Building.objects.filter(area__in=area_qs)
            building_count = building_qs.count()
            units_sum = calculate_total_units_sum(building_qs)
            return {"building_count": building_count, "units_sum": units_sum}
        else:
            building_qs = Building.objects.filter(english_name__icontains=search_str)
            if building_qs.exists():
                building_count = building_qs.count()
                units_sum = calculate_total_units_sum(building_qs)
                return {"building_count": building_count, "units_sum": units_sum}
            else:
                project_qs = Project.objects.all()
                building_count = project_qs.count()
                units_sum = sum(p.total_units or 0 for p in project_qs)
                return {"building_count": building_count, "units_sum": units_sum}
    else:
        building_qs = Building.objects.all()
        building_count = building_qs.count()
        units_sum = sum(b.total_units or 0 for b in building_qs)
        return {"building_count": building_count, "units_sum": units_sum}


def calc_and_save_search_log(
    transaction_type: str,
    search_substring: Optional[str],
    property_components: Optional[List[str]],
    period_str: Optional[str] = None,
    return_dict: bool = False,  # if True, return dict of aggregated values instead of log_obj
    use_cache: bool = True,  # if True, use cache for expensive calculations
) -> Union[SearchTransactionsLog, dict]:
    """
    1) Builds a queryset of MergedTransaction for the given filters.
    2) Splits the data into a 'current period' and a 'previous period' (e.g. current month vs. previous month).
    3) Calculates metrics:
       - averagePrice_value: arithmetic mean price (current period)
       - averagePrice_dynamic: percent difference between current and previous average price
       - averagePrice_versus: ratio of the current value compared to the reference average (area or Dubai)
       - medianPrice_value: median price (current period)
       - medianPrice_dynamic: percent difference between current and previous median price
       - medianPrice_versus: ratio of the current value compared to the reference average (area or Dubai)
       - averagePricePerSQM_value: current average price per sq.ft. (avg price / avg area)
       - averagePricePerSQM_dynamic: percent difference for average price per sq.ft.
       - averagePricePerSQM_versus: ratio of the current value compared to the reference average (area or Dubai)
       - priceRange_range: string "(min, max)" for current period
       - priceRange_dynamic: percent change in the price range span (current vs. previous)
       - priceRange_versus: ratio of the current range compared to the reference range (area or Dubai)
       - deals_value: count of transactions (current period)
       - deals_dynamic: percent change in transaction count (current vs. previous)
       - deals_versus: ratio of the current value compared to the reference average (area or Dubai)
       - dealsVolume_value: sum of transaction prices (current period)
       - dealsVolume_dynamic: percent change in deals volume (current vs. previous)
       - dealsVolume_versus: ratio of the current value compared to the reference average (area or Dubai)
       - liquidity_value: (special liquidity calc)
       - liquidity_dynamic: percent change in liquidity_value (current vs. previous)
       - liquidity_versus: ratio of the current value compared to the reference average (area or Dubai)

       - total_buildings: computed via compute_total_buildings() based on searchSubstring
       - total_deals: same as deals_value
       - total_properties: sum of total_units across buildings (current period)
       - growth_dynamic_percent: same as deals_dynamic (percent change in count)

    4) If return_dict is False, saves these metrics in a SearchTransactionsLog record and returns it.
       Otherwise, returns a dictionary with the computed values.

    5) VERSUS LOGIC:
       - If searching for a building/project: VERSUS = VALUE for building/project divided by average for the AREA
       - If searching for an area: VERSUS = VALUE for area divided by average for all of Dubai
       - For PRICE_RANGE: VERSUS is calculated based on range span instead of value
       - This applies to: AVERAGE_PRICE, MEDIAN_PRICE, AVERAGE_PRICE_PER_SQM, PRICE_RANGE, DEALS_VOLUME, LIQUIDITY

    6) CACHING:
       - Expensive calculations (especially reference values and versus metrics) are cached for a day
       - Cache key is based on the input parameters and period boundaries
    """
    # First check if search_substring matches an existing building, project, or area
    # Only cache results for valid entities, not arbitrary user searches
    should_use_cache = False
    if use_cache and search_substring and search_substring.strip():
        search_str = search_substring.strip()
        # Check if it's a valid building
        building_exists = Building.objects.filter(
            english_name__icontains=search_str
        ).exists()
        if building_exists:
            should_use_cache = True

        # Check if it's a valid project
        if not should_use_cache:
            project_exists = Project.objects.filter(
                english_name__icontains=search_str
            ).exists()
            if project_exists:
                should_use_cache = True

        # Check if it's a valid area
        if not should_use_cache:
            area_exists = Area.objects.filter(
                Q(name_en__icontains=search_str) | Q(name_ar__icontains=search_str)
            ).exists()
            if area_exists:
                should_use_cache = True
    else:
        # If no search substring is provided, we're getting all Dubai data
        # which is definitely worth caching
        should_use_cache = use_cache

    # Generate a cache key based on input parameters
    cache_key_params = {
        "transaction_type": transaction_type,
        "search_substring": search_substring,
        "property_components": property_components if property_components else [],
        "period_str": period_str if period_str else "1 month",
    }
    cache_key = f"stats_aggregation_{hashlib.md5(json.dumps(cache_key_params, sort_keys=True).encode()).hexdigest()}"

    # Try to get the cached result
    if should_use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            # If we need to save to the database but have a cached result, just create the DB entry
            if not return_dict:
                log_obj = SearchTransactionsLog.objects.create(
                    transaction_type=transaction_type,
                    search_substring=search_substring or "",
                    property_components=property_components or [],
                    period=period_str if period_str else "1 month",
                    avg_price=cached_result["averagePrice_value"],
                    transaction_count=cached_result["deals_value"],
                    transaction_count_change_percent=cached_result["deals_dynamic"],
                    median_price=cached_result["medianPrice_value"],
                    median_price_change_percent=cached_result["medianPrice_dynamic"],
                    avg_price_per_sqft=cached_result["averagePricePerSQM_value"],
                    building_count=cached_result["total_buildings"],
                    total_units=cached_result["total_properties"],
                    price_range=cached_result["priceRange_range"],
                    special_liquidity_calc=cached_result["liquidity_value"],
                )
                return log_obj
            return cached_result

    # 1) Build the base queryset (without date filtering)
    qs_all = _build_transactions_queryset(
        transaction_type=transaction_type,
        search_substring=search_substring,
        property_components=property_components,
        periods=None,
    ).select_related("building__project")

    # Determine period (default "1 month")
    if not period_str:
        period_str = "1 month"

    # 2) Get current period and previous period boundaries
    start_current, end_current = _get_period_range(period_str)
    delta_current = end_current - start_current
    end_previous = start_current
    start_previous = end_previous - delta_current

    # 3) Split the queryset into current and previous period lists
    qs_current = qs_all.filter(
        date_of_transaction__gte=start_current, date_of_transaction__lte=end_current
    )
    qs_previous = qs_all.filter(
        date_of_transaction__gte=start_previous, date_of_transaction__lte=end_previous
    )
    current_list = list(qs_current)
    prev_list = list(qs_previous)

    # Helper functions:
    def average_price(objs):
        prices = [float(o.transaction_price or 0) for o in objs]
        return sum(prices) / len(prices) if prices else 0.0

    def median_price(objs):
        prices = [float(o.transaction_price or 0) for o in objs]
        return statistics.median(prices) if prices else 0.0

    def avg_area(objs):
        areas = [float(o.sqm or 0) for o in objs]
        return sum(areas) / len(areas) if areas else 0.0

    def price_range_span(objs):
        prices = [float(o.transaction_price or 0) for o in objs]
        if prices:
            return min(prices), max(prices)
        return (0.0, 0.0)

    def sum_deals_volume(objs):
        return sum(float(o.transaction_price or 0) for o in objs)

    def percent_change(current, previous):
        if previous == 0 and current > 0:
            return 100.0
        elif previous == 0:
            return 0.0
        return (current - previous) / previous * 100.0

    def calculate_versus(value, reference_value):
        if reference_value == 0:
            return 0.0
        return 100.0 * (value / reference_value)

    # 4) Compute metrics for the current period
    curr_avg_price = average_price(current_list)
    curr_count = len(current_list)
    curr_median = median_price(current_list)
    curr_avg_area = avg_area(current_list)
    curr_avg_price_per_sqft = (
        curr_avg_price / curr_avg_area if curr_avg_area > 0 else 0.0
    )
    curr_min_price, curr_max_price = price_range_span(current_list)
    price_range_str = f"({curr_min_price}, {curr_max_price})"
    curr_price_range_span = curr_max_price - curr_min_price
    curr_deals_volume = sum_deals_volume(current_list)

    # 5) Compute metrics for the previous period
    prev_avg_price = average_price(prev_list)
    prev_count = len(prev_list)
    prev_median = median_price(prev_list)
    prev_avg_area = avg_area(prev_list)
    prev_avg_price_per_sqft = (
        prev_avg_price / prev_avg_area if prev_avg_area > 0 else 0.0
    )
    prev_min_price, prev_max_price = price_range_span(prev_list)
    prev_price_range_span = prev_max_price - prev_min_price
    prev_deals_volume = sum_deals_volume(prev_list)

    # Compute percentage differences
    averagePrice_dynamic = percent_change(curr_avg_price, prev_avg_price)
    median_change_percent = percent_change(curr_median, prev_median)
    averagePricePerSQM_dynamic = percent_change(
        curr_avg_price_per_sqft, prev_avg_price_per_sqft
    )
    price_range_dynamic = percent_change(curr_price_range_span, prev_price_range_span)
    deals_dynamic = percent_change(curr_count, prev_count)
    dealsVolume_dynamic = percent_change(curr_deals_volume, prev_deals_volume)

    # Define count_change_percent as the same as deals_dynamic (percent change in transaction count)
    count_change_percent = deals_dynamic

    # 6) Compute special liquidity for the current period.
    #
    # Логика:
    #  - Собираем все (year, month) для транзакций из current_list
    #  - Для каждого (year, month) находим УНИКАЛЬНЫЕ building_ids
    #  - Для каждого building, если total_units>0, берём liquidity_parameter_one
    #    и считаем ratio = liq / total_units
    #  - Считаем среднее ratio по зданиям этого месяца => monthly_avg
    #  - Собираем monthly_avg в список monthly_values
    #  - liquidity_value = среднее(monthly_values) (если не пустой)
    #

    def compute_liquidity_value_for_period(tx_list: List):
        # 1) Группируем транзакции по (year, month)
        month_buildings_map = defaultdict(set)
        for tx in tx_list:
            if tx.building_id and tx.date_of_transaction:
                yy = tx.date_of_transaction.year
                mm = tx.date_of_transaction.month
                month_buildings_map[(yy, mm)].add(tx.building_id)

        # 2) Для каждого (year, month), собираем ratio = liq_param / total_units
        monthly_averages = []
        for (yy, mm), bld_ids in month_buildings_map.items():
            ratios = []
            for b_id in bld_ids:
                bld_liq = BuildingLiquidityParameterOne.objects.filter(
                    building_id=b_id, year=yy, month=mm
                ).first()
                if not bld_liq:
                    continue
                liquidity_val = float(bld_liq.liquidity_parameter_one or 0)
                # Посмотрим на total_units
                building_obj = (
                    Building.objects.filter(pk=b_id).select_related("project").first()
                )
                if not building_obj:
                    continue
                # Считаем реальный total_units
                if building_obj.total_units and building_obj.total_units > 0:
                    tu = building_obj.total_units
                elif building_obj.project and building_obj.project.total_units:
                    tu = building_obj.project.total_units
                else:
                    tu = 0

                if tu > 0:  # только если >0
                    ratio = liquidity_val / tu  # liq / total_units
                    ratios.append(ratio)
            if ratios:
                monthly_avg = sum(ratios) / len(ratios)
                monthly_averages.append(monthly_avg)

        if monthly_averages:
            return sum(monthly_averages) / len(monthly_averages)
        else:
            return 0.0

    liquidity_value = compute_liquidity_value_for_period(current_list)
    liquidity_value_prev = compute_liquidity_value_for_period(prev_list)
    liquidity_dynamic = percent_change(liquidity_value, liquidity_value_prev)

    # 7) Other aggregated fields:
    # Use the new helper function to compute total_buildings based on searchSubstring.
    total_buildings_dict = compute_total_buildings(search_substring)

    total_buildings = total_buildings_dict["building_count"]
    total_units_sum = total_buildings_dict["units_sum"]

    total_deals = curr_count
    total_properties = total_units_sum

    growth_dynamic_percent = deals_dynamic  # percent change in transaction count

    # 8) Calculate reference values for VERSUS metric
    # This is the expensive part that benefits most from caching

    # Generate cache key for reference values
    reference_cache_key = f"reference_values_{transaction_type}_{start_current.isoformat()}_{end_current.isoformat()}_"
    reference_cache_key += f"{hashlib.md5(json.dumps(property_components if property_components else [], sort_keys=True).encode()).hexdigest()}"

    # Try to get cached reference values
    cached_reference = None
    if should_use_cache:
        cached_reference = cache.get(reference_cache_key)

    if cached_reference:
        # Use cached reference values
        reference_avg_price = cached_reference["avg_price"]
        reference_median = cached_reference["median"]
        reference_avg_price_per_sqft = cached_reference["avg_price_per_sqft"]
        reference_price_range_span = cached_reference["price_range_span"]
        reference_count = cached_reference["count"]
        reference_deals_volume = cached_reference["deals_volume"]
        reference_liquidity = cached_reference["liquidity"]

        # Check if we have cached area reference values for this building/project
        if search_substring and search_substring.strip():
            search_str = search_substring.strip()
            area_reference_cache_key = (
                f"{reference_cache_key}_{hashlib.md5(search_str.encode()).hexdigest()}"
            )
            area_cached_reference = cache.get(area_reference_cache_key)

            if area_cached_reference:
                is_building_or_project_search = area_cached_reference[
                    "is_building_or_project_search"
                ]
                if is_building_or_project_search:
                    reference_avg_price = area_cached_reference["avg_price"]
                    reference_median = area_cached_reference["median"]
                    reference_avg_price_per_sqft = area_cached_reference[
                        "avg_price_per_sqft"
                    ]
                    reference_price_range_span = area_cached_reference[
                        "price_range_span"
                    ]
                    reference_count = area_cached_reference["count"]
                    reference_deals_volume = area_cached_reference["deals_volume"]
                    reference_liquidity = area_cached_reference["liquidity"]
    else:
        # Determine if the search is for a building/project or an area
        is_building_or_project_search = False
        reference_area_ids = []

        if search_substring and search_substring.strip():
            search_str = search_substring.strip()
            # Check if it's a building search
            building_qs = Building.objects.filter(english_name__icontains=search_str)
            if building_qs.exists():
                is_building_or_project_search = True
                # Get the areas of the buildings
                reference_area_ids = list(
                    building_qs.values_list("area_id", flat=True).distinct()
                )

            # Check if it's a project search
            if not is_building_or_project_search:
                project_qs = Project.objects.filter(english_name__icontains=search_str)
                if project_qs.exists():
                    is_building_or_project_search = True
                    # Get buildings associated with this project, then get their areas
                    buildings_in_projects = Building.objects.filter(
                        project__in=project_qs
                    )
                    reference_area_ids = list(
                        buildings_in_projects.values_list(
                            "area_id", flat=True
                        ).distinct()
                    )

        # First, cache the all Dubai reference values which are most expensive to compute
        all_dubai_reference_transactions_qs = (
            _build_transactions_queryset(
                transaction_type=transaction_type,
                search_substring=None,
                property_components=property_components,
                periods=None,
            )
            .filter(
                date_of_transaction__gte=start_current,
                date_of_transaction__lte=end_current,
            )
            .select_related("building__project")
        )

        all_dubai_reference_list = list(all_dubai_reference_transactions_qs)

        # Calculate all Dubai reference metrics
        all_dubai_reference_avg_price = average_price(all_dubai_reference_list)
        all_dubai_reference_median = median_price(all_dubai_reference_list)
        all_dubai_reference_avg_area = avg_area(all_dubai_reference_list)
        all_dubai_reference_avg_price_per_sqft = (
            all_dubai_reference_avg_price / all_dubai_reference_avg_area
            if all_dubai_reference_avg_area > 0
            else 0.0
        )
        all_dubai_reference_min_price, all_dubai_reference_max_price = price_range_span(
            all_dubai_reference_list
        )
        all_dubai_reference_price_range_span = (
            all_dubai_reference_max_price - all_dubai_reference_min_price
        )
        all_dubai_reference_count = len(all_dubai_reference_list)
        all_dubai_reference_deals_volume = sum_deals_volume(all_dubai_reference_list)
        all_dubai_reference_liquidity = compute_liquidity_value_for_period(
            all_dubai_reference_list
        )

        # Cache the all Dubai reference values
        all_dubai_reference_data = {
            "avg_price": all_dubai_reference_avg_price,
            "median": all_dubai_reference_median,
            "avg_price_per_sqft": all_dubai_reference_avg_price_per_sqft,
            "price_range_span": all_dubai_reference_price_range_span,
            "count": all_dubai_reference_count,
            "deals_volume": all_dubai_reference_deals_volume,
            "liquidity": all_dubai_reference_liquidity,
        }

        # Always cache Dubai reference values regardless of search substring
        # as these are expensive to compute and used by all queries
        if use_cache:
            cache.set(
                reference_cache_key, all_dubai_reference_data, 60 * 60 * 24
            )  # Cache for 1 day

        # If this is a building/project search, calculate area-specific reference values
        if is_building_or_project_search and reference_area_ids:
            # For building/project, reference is the area
            area_reference_transactions_qs = (
                _build_transactions_queryset(
                    transaction_type=transaction_type,
                    search_substring=None,
                    property_components=property_components,
                    periods=None,
                )
                .filter(
                    area_id__in=reference_area_ids,
                    date_of_transaction__gte=start_current,
                    date_of_transaction__lte=end_current,
                )
                .select_related("building__project")
            )

            area_reference_list = list(area_reference_transactions_qs)

            # Calculate area reference metrics
            area_reference_avg_price = average_price(area_reference_list)
            area_reference_median = median_price(area_reference_list)
            area_reference_avg_area = avg_area(area_reference_list)
            area_reference_avg_price_per_sqft = (
                area_reference_avg_price / area_reference_avg_area
                if area_reference_avg_area > 0
                else 0.0
            )
            area_reference_min_price, area_reference_max_price = price_range_span(
                area_reference_list
            )
            area_reference_price_range_span = (
                area_reference_max_price - area_reference_min_price
            )
            area_reference_count = len(area_reference_list)
            area_reference_deals_volume = sum_deals_volume(area_reference_list)
            area_reference_liquidity = compute_liquidity_value_for_period(
                area_reference_list
            )

            # Use area references for versus calculations
            reference_avg_price = area_reference_avg_price
            reference_median = area_reference_median
            reference_avg_price_per_sqft = area_reference_avg_price_per_sqft
            reference_price_range_span = area_reference_price_range_span
            reference_count = area_reference_count
            reference_deals_volume = area_reference_deals_volume
            reference_liquidity = area_reference_liquidity

            # Cache area-specific reference values
            # These are associated with specific areas, so we always cache them
            if use_cache and search_substring and search_substring.strip():
                search_str = search_substring.strip()
                area_reference_cache_key = f"{reference_cache_key}_{hashlib.md5(search_str.encode()).hexdigest()}"
                area_reference_data = {
                    "is_building_or_project_search": True,
                    "avg_price": area_reference_avg_price,
                    "median": area_reference_median,
                    "avg_price_per_sqft": area_reference_avg_price_per_sqft,
                    "price_range_span": area_reference_price_range_span,
                    "count": area_reference_count,
                    "deals_volume": area_reference_deals_volume,
                    "liquidity": area_reference_liquidity,
                }
                cache.set(
                    area_reference_cache_key, area_reference_data, 60 * 60 * 24
                )  # Cache for 1 day
        else:
            # For area/general search, use all Dubai references
            reference_avg_price = all_dubai_reference_avg_price
            reference_median = all_dubai_reference_median
            reference_avg_price_per_sqft = all_dubai_reference_avg_price_per_sqft
            reference_price_range_span = all_dubai_reference_price_range_span
            reference_count = all_dubai_reference_count
            reference_deals_volume = all_dubai_reference_deals_volume
            reference_liquidity = all_dubai_reference_liquidity

    # Calculate versus metrics
    averagePrice_versus = calculate_versus(curr_avg_price, reference_avg_price)
    medianPrice_versus = calculate_versus(curr_median, reference_median)
    averagePricePerSQM_versus = calculate_versus(
        curr_avg_price_per_sqft, reference_avg_price_per_sqft
    )
    priceRange_versus = calculate_versus(
        curr_price_range_span, reference_price_range_span
    )
    deals_versus = calculate_versus(curr_count, reference_count)
    dealsVolume_versus = calculate_versus(curr_deals_volume, reference_deals_volume)
    liquidity_versus = calculate_versus(liquidity_value, reference_liquidity)

    # Prepare aggregated result dictionary:
    result_dict = {
        "averagePrice_value": curr_avg_price,
        "averagePrice_dynamic": averagePrice_dynamic,
        "averagePrice_versus": averagePrice_versus,
        "medianPrice_value": curr_median,
        "medianPrice_dynamic": median_change_percent,
        "medianPrice_versus": medianPrice_versus,
        "averagePricePerSQM_value": curr_avg_price_per_sqft,
        "averagePricePerSQM_dynamic": averagePricePerSQM_dynamic,
        "averagePricePerSQM_versus": averagePricePerSQM_versus,
        "priceRange_range": price_range_str,
        "priceRange_dynamic": price_range_dynamic,
        "priceRange_versus": priceRange_versus,
        "deals_value": curr_count,
        "deals_dynamic": deals_dynamic,
        "deals_versus": deals_versus,
        "dealsVolume_value": curr_deals_volume,
        "dealsVolume_dynamic": dealsVolume_dynamic,
        "dealsVolume_versus": dealsVolume_versus,
        "liquidity_value": liquidity_value,
        "liquidity_dynamic": liquidity_dynamic,
        "liquidity_versus": liquidity_versus,
        "total_buildings": total_buildings,
        "total_deals": total_deals,
        "total_properties": total_properties,
        "growth_dynamic_percent": growth_dynamic_percent,
    }

    # Cache the final result only if it matches a valid entity
    if should_use_cache:
        cache.set(cache_key, result_dict, 60 * 60 * 24)  # Cache for 1 day

    # 9) If return_dict is True, return the dictionary; otherwise, save and return the SearchTransactionsLog instance.
    if return_dict:
        return result_dict
    else:
        log_obj = SearchTransactionsLog.objects.create(
            transaction_type=transaction_type,
            search_substring=search_substring or "",
            property_components=property_components or [],
            period=period_str,
            avg_price=curr_avg_price,
            transaction_count=curr_count,
            transaction_count_change_percent=count_change_percent,
            median_price=curr_median,
            median_price_change_percent=median_change_percent,
            avg_price_per_sqft=curr_avg_price_per_sqft,
            building_count=total_buildings,
            total_units=total_units_sum,
            price_range=price_range_str,
            special_liquidity_calc=liquidity_value,
        )
        return log_obj

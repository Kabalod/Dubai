import datetime

from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Max
from django.db.models import Min
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.db import models

from .models import Area
from .models import Building
from .models import MergedRentalTransaction
from .models import MergedTransaction
from .models import Project


def rental_transactions_list(request):
    # Получаем параметры фильтрации из GET-запроса
    search_query = request.GET.get("q", "").strip()
    search_period = request.GET.get("period", "").strip()
    search_rooms = request.GET.get("rooms", "").strip()
    sort_by_param = request.GET.get("sort", "")
    order_param = request.GET.get("order", "asc").lower()

    # Если автокомплит выбрал элемент, получаем тип и id
    object_type = request.GET.get("object_type", "").strip()
    object_id = request.GET.get("object_id", "").strip()

    # Базовый queryset с предзагрузкой связанных объектов
    transactions = MergedRentalTransaction.objects.select_related(
        "area", "building", "project", "project__developer"
    ).all()

    # Логика расширения period, включая "10 years"
    period_includes = {
        "1 week": ["1 week"],
        "1 month": ["1 month"],
        "3 months": ["3 months", "1 month"],
        "6 months": ["6 months", "3 months", "1 month"],
        "1 year": ["1 year", "6 months", "3 months", "1 month"],
        "2 year": ["2 year", "1 year", "6 months", "3 months", "1 month"],
        "YTD": ["YTD", "1 year", "6 months", "3 months", "1 month"],
        "10 years": ["10 years", "2 year", "1 year", "6 months", "3 months", "1 month"],
    }
    if search_period:
        periods_to_include = period_includes.get(search_period, [search_period])
        transactions = transactions.filter(period__in=periods_to_include)

    # Фильтрация по количеству комнат
    if search_rooms:
        transactions = transactions.filter(number_of_rooms=search_rooms)

    # Эта переменная нужна для ROI-фильтрации (см. ниже):
    step1_area = None
    step2_building = None
    step3_project = None

    selected_object_data = {}
    branch_stats = None  # покажем в шаблоне, если мы "не" выбрали object_type

    # --- 1. Если автокомплитом выбрали объект ---
    if object_type and object_id:
        if object_type == "area":
            try:
                selected_area = Area.objects.get(id=object_id)
                transactions = transactions.filter(area=selected_area)
                search_query = selected_area.name_en or ""
                buildings_qs = Building.objects.filter(area=selected_area)
            except Area.DoesNotExist:
                buildings_qs = Building.objects.none()

        elif object_type == "building":
            try:
                selected_building = Building.objects.get(id=object_id)
                transactions = transactions.filter(building=selected_building)
                search_query = selected_building.english_name or ""
                buildings_qs = Building.objects.filter(id=selected_building.id)
            except Building.DoesNotExist:
                buildings_qs = Building.objects.none()

        elif object_type == "project":
            try:
                selected_project = Project.objects.get(id=object_id)
                transactions = transactions.filter(project=selected_project)
                search_query = selected_project.english_name or ""
                buildings_qs = Building.objects.filter(project=selected_project)
            except Project.DoesNotExist:
                buildings_qs = Building.objects.none()

        else:
            buildings_qs = Building.objects.none()

        # Для объекта area/building/project считаем три метрики
        count_deals = transactions.count()
        count_buildings = buildings_qs.count()
        total_units = buildings_qs.aggregate(total=Sum("total_units"))["total"] or 0

        selected_object_data = {
            "count_deals": count_deals,
            "count_buildings": count_buildings,
            "total_units": total_units,
        }

    # --- 2. Иначе: классический поиск по substring (area->building->project) ---
    else:
        # branch_stats для вывода в шаблоне
        branch_stats = {
            "search_building_count": 0,
            "search_total_units": 0,
            "ratio_3": None,
        }
        qs_area = transactions.filter(area__name_en__icontains=search_query)
        if qs_area.exists():
            # У нас есть Area
            first_area = qs_area.first().area
            step1_area = first_area  # для ROI
            transactions = transactions.filter(area=first_area)
            search_query = first_area.name_en or ""

            # Посчитаем, сколько Buildings содержат эту подстроку
            # (если у вас другая логика, подправьте)
            # Здесь: area__name_en__icontains=?
            area_buildings = Building.objects.filter(
                area__name_en__icontains=first_area.name_en
            )
            branch_stats["search_building_count"] = area_buildings.count()
            branch_stats["search_total_units"] = (
                area_buildings.aggregate(s=Sum("total_units"))["s"] or 0
            )

        else:
            qs_building = transactions.filter(
                building__english_name__icontains=search_query
            )
            if qs_building.exists():
                # У нас есть Building
                first_building = qs_building.first().building
                step2_building = first_building  # для ROI
                transactions = transactions.filter(building=first_building)
                search_query = first_building.english_name or ""

                # Сколько Buildings содержат данную подстроку в english_name
                bbuildings = Building.objects.filter(
                    english_name__icontains=first_building.english_name
                )
                branch_stats["search_building_count"] = bbuildings.count()
                branch_stats["search_total_units"] = (
                    bbuildings.aggregate(s=Sum("total_units"))["s"] or 0
                )

            else:
                qs_project = transactions.filter(
                    project__english_name__icontains=search_query
                )
                if qs_project.exists():
                    # У нас есть Project
                    first_project = qs_project.first().project
                    step3_project = first_project  # для ROI
                    transactions = transactions.filter(project=first_project)
                    search_query = first_project.english_name or ""

                    # Сколько Buildings содержат подстроку в project__english_name
                    pbuildings = Building.objects.filter(
                        project__english_name__icontains=first_project.english_name
                    )
                    branch_stats["search_building_count"] = pbuildings.count()
                    branch_stats["search_total_units"] = (
                        pbuildings.aggregate(s=Sum("total_units"))["s"] or 0
                    )

        # Рассчитаем ratio_3 = deals_count / max_total_units / number_of_months
        deals_count_local = transactions.count()

        def parse_period_local(p_str):
            p_str = p_str.lower().strip()
            if "week" in p_str:
                return 0.25
            elif "month" in p_str:
                try:
                    num = float(p_str.split()[0])
                    return num
                except:
                    return None
            elif "year" in p_str:
                try:
                    num = float(p_str.split()[0])
                    return num * 12
                except:
                    return None
            elif p_str == "ytd":
                return datetime.date.today().month
            elif "10 years" in p_str:
                return 120.0
            else:
                return None

        number_of_months_local = (
            parse_period_local(search_period) if search_period else None
        )
        max_tu = branch_stats["search_total_units"] or 0

        if max_tu > 0 and number_of_months_local and number_of_months_local > 0:
            ratio_3 = deals_count_local / max_tu / number_of_months_local
            branch_stats["ratio_3"] = ratio_3

    # --- Сортировка ---
    sort_fields = {
        "contract_id": "contract_id",
        "area": "area__name_en",
        "rooms": "number_of_rooms",
        "annual": "annual_amount",
        "meter": "meter_sale_price",
        "developer": "project__developer__english_name",
        "rental_range": "contract_start_date",
        "building": "building_name",
        "project": "project__english_name",
        "sqm": "sqm",
    }
    if sort_by_param in sort_fields:
        order_field = sort_fields[sort_by_param]
        if order_param == "desc":
            order_field = "-" + order_field
        transactions = transactions.order_by(order_field)

    # Пагинация
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # --- Глобальные агрегаты ---
    aggs = transactions.aggregate(
        avg_price=Avg("annual_amount"),
        total_deal_volume=Sum("annual_amount"),
        avg_sqm=Avg("sqm"),
        count_deals=Count("id"),
        min_meter=Min("meter_sale_price"),
        max_meter=Max("meter_sale_price"),
        avg_meter=Avg("meter_sale_price"),
    )
    
    # Убираем проблемный расчет медианы - он загружает все данные в память
    # prices = list(
    #     transactions.order_by("annual_amount").values_list("annual_amount", flat=True)
    # )
    # if prices:
    #     n = len(prices)
    #     if n % 2 == 1:
    #         median_price = prices[n // 2]
    #     else:
    #         median_price = (prices[n // 2 - 1] + prices[n // 2]) / 2
    # else:
    #     median_price = None
    median_price = None  # Временно отключаем для оптимизации

    deals_count_global = aggs["count_deals"] or 0

    # Оптимизируем подсчет зданий - заменяем цикл на один запрос
    from django.db.models import Count as CountFunc
    
    # Получаем количество зданий одним запросом
    building_stats = transactions.aggregate(
        direct_buildings=CountFunc('building', distinct=True),
        projects_without_buildings=CountFunc('project', distinct=True, filter=models.Q(building__isnull=True))
    )
    
    direct_building_count = building_stats['direct_buildings'] or 0
    
    # Получаем количество зданий в проектах без зданий одним запросом
    project_ids_missing_building = (
        transactions.filter(building__isnull=True, project__isnull=False)
        .values_list("project", flat=True)
        .distinct()
    )
    
    # Оптимизируем: используем один запрос вместо цикла
    if project_ids_missing_building:
        sum_buildings_from_project = Building.objects.filter(
            project_id__in=project_ids_missing_building
        ).count()
    else:
        sum_buildings_from_project = 0
        
    combined_building_count = direct_building_count + sum_buildings_from_project

    # Кол-во проектов
    project_count = (
        transactions.filter(project__isnull=False)
        .values_list("project", flat=True)
        .distinct()
        .count()
    )

    # Сумма квартир (no_of_prop)
    apartments_sum = (
        transactions.aggregate(total_apartments=Sum("no_of_prop"))["total_apartments"]
        or 0
    )

    # Ещё раз parse_period_global для ratio_metric
    def parse_period_global(p_str):
        p_str = p_str.lower().strip()
        if "week" in p_str:
            return 0.25
        elif "month" in p_str:
            try:
                num = float(p_str.split()[0])
                return num
            except:
                return None
        elif "year" in p_str:
            try:
                num = float(p_str.split()[0])
                return num * 12
            except:
                return None
        elif p_str == "ytd":
            return datetime.date.today().month
        elif "10 years" in p_str:
            return 120.0
        else:
            return None

    number_of_months_global = (
        parse_period_global(search_period) if search_period else None
    )
    if number_of_months_global and number_of_months_global > 0:
        ratio_metric = (
            f"{deals_count_global} / {apartments_sum} / {number_of_months_global}"
        )
    else:
        ratio_metric = f"{deals_count_global} / {apartments_sum} / –"

    # Сумма total_units всех проектов
    project_ids = (
        transactions.filter(project__isnull=False)
        .values_list("project", flat=True)
        .distinct()
    )
    sum_total_units = (
        Project.objects.filter(id__in=list(project_ids)).aggregate(
            total=Sum("total_units")
        )["total"]
        or 0
    )

    # --- ROI ---
    # Средняя аренда = aggs['avg_price']
    rental_avg_price = aggs["avg_price"] or 0
    # Средняя продажа: MergedTransaction с transaction_type="sales", фильтр по substring и по search_period
    sales_qs = MergedTransaction.objects.filter(transaction_type="sales")

    # Фильтр substring (area->building->project) — ориентируемся на step1_area, step2_building, step3_project
    if search_query:
        if step1_area:
            sales_qs = sales_qs.filter(building__area=step1_area)
        else:
            if step2_building:
                sales_qs = sales_qs.filter(building=step2_building)
            else:
                if step3_project:
                    sales_qs = sales_qs.filter(building__project=step3_project)
                else:
                    # никаких шагов не выполнено — pass
                    pass

    # Фильтр по period (тот же periods_to_include)
    if search_period:
        sales_periods = period_includes.get(search_period, [search_period])
        sales_qs = sales_qs.filter(period__in=sales_periods)

    avg_sales_price = sales_qs.aggregate(avg_sp=Avg("transaction_price"))["avg_sp"] or 0
    roi_value = None
    if avg_sales_price != 0:
        # Приводим к float, если avg_sales_price = Decimal
        roi_value = float(rental_avg_price) / float(avg_sales_price)

    # Финальный контекст
    period_options = [
        "1 week",
        "1 month",
        "3 months",
        "6 months",
        "1 year",
        "2 year",
        "YTD",
        "10 years",
    ]
    room_options = ["studio", "1 B/R", "2 B/R", "3 B/R", "4 B/R"]

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "search_period": search_period,
        "search_rooms": search_rooms,
        "sort_by": sort_by_param,
        "order": order_param,
        # Глобальные агрегаты
        "aggregates": {
            "avg_price": aggs["avg_price"],
            "median_price": median_price,
            "avg_sqm": aggs["avg_sqm"],
            "count_deals": deals_count_global,
            "total_deal_volume": aggs["total_deal_volume"],
            "min_meter": aggs["min_meter"],
            "max_meter": aggs["max_meter"],
            "avg_meter": aggs["avg_meter"],
            "selected_object": selected_object_data,
            "combined_building_count": combined_building_count,
            "project_count": project_count,
            "ratio_metric": ratio_metric,
            "sum_total_units": sum_total_units,
            "roi_value": roi_value,
        },
        # Статистика поиска, если не выбрали объект автокомплитом
        "branch_stats": branch_stats,
        "period_options": period_options,
        "room_options": room_options,
    }
    return render(request, "main/rental_transactions_list.html", context)


def autocomplete_suggestions(request):
    """Возвращает JSON с подсказками для автокомплита: Areas, Buildings, Projects."""
    query = request.GET.get("q", "").strip()
    suggestions = {"areas": [], "buildings": [], "projects": []}
    if query:
        areas = Area.objects.filter(name_en__icontains=query)[:5]
        suggestions["areas"] = [{"id": a.id, "name": a.name_en} for a in areas]
        buildings = Building.objects.filter(english_name__icontains=query)[:5]
        suggestions["buildings"] = [
            {"id": b.id, "name": b.english_name} for b in buildings
        ]
        projects = Project.objects.filter(english_name__icontains=query)[:5]
        suggestions["projects"] = [
            {"id": p.id, "name": p.english_name} for p in projects
        ]
    return JsonResponse(suggestions)

from django.shortcuts import render
from django.db.models import Q, Avg, Count, Case, When, FloatField
from django.core.paginator import Paginator
from django.http import JsonResponse
from django_tables2 import RequestConfig
from .models import Property, Building, AREAS_WITH_PROPERTY
from .tables import PropertyTable
from django.conf import settings
import datetime
import json


def property_list_tables2(request):
    """Главная страница со списком недвижимости с Django Tables 2"""
    
    # Базовый queryset с предзагрузкой связанных объектов и метрик
    properties = Property.objects.select_related('building', 'metrics')
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(display_address__icontains=search_query) |
            Q(building__name__icontains=search_query) |
            Q(agent_name__icontains=search_query) |
            Q(broker_name__icontains=search_query)
        )
    
    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Фильтрация по количеству спален
    bedrooms = request.GET.get('bedrooms')
    if bedrooms:
        try:
            properties = properties.filter(bedrooms=int(bedrooms))
        except ValueError:
            pass
    
    # Фильтрация по типу (продажа/аренда)
    price_duration = request.GET.get('price_duration')
    if price_duration in ['sell', 'rent']:
        properties = properties.filter(price_duration=price_duration)
    
    # Фильтрация по району
    area = request.GET.get('area')
    if area:
        properties = properties.filter(building__area__icontains=area)
    
    # Фильтрация по зданию
    building_name = request.GET.get('building')
    if building_name:
        properties = properties.filter(building__name__icontains=building_name)
    
    # Фильтрация по ROI
    min_roi = request.GET.get('min_roi')
    max_roi = request.GET.get('max_roi')
    if min_roi:
        try:
            properties = properties.filter(roi__gte=float(min_roi))
        except ValueError:
            pass
    if max_roi:
        try:
            properties = properties.filter(roi__lte=float(max_roi))
        except ValueError:
            pass
    
    # Создаем таблицу
    table = PropertyTable(properties)
    
    # Настраиваем таблицу с параметрами запроса
    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    
    # Получаем список разрешенных районов
    available_areas = sorted(AREAS_WITH_PROPERTY.keys())
    
    buildings = Building.objects.values_list('name', flat=True).distinct().order_by('name')
    buildings = [building for building in buildings if building]  # Убираем пустые значения
    
    bedroom_choices = Property.objects.values_list('bedrooms', flat=True).distinct().order_by('bedrooms')
    bedroom_choices = [br for br in bedroom_choices if br is not None]
    
    context = {
        'table': table,
        'search_query': search_query,
        'available_areas': available_areas,
        'buildings': buildings,
        'bedroom_choices': bedroom_choices,
        'current_filters': {
            'min_price': min_price,
            'max_price': max_price,
            'bedrooms': bedrooms,
            'price_duration': price_duration,
            'area': area,
            'building': building_name,
            'min_roi': min_roi,
            'max_roi': max_roi,
        },
        'total_properties': properties.count(),
    }
    
    return render(request, 'properties/property_list_tables2.html', context)


def property_list(request):
    """Главная страница со списком недвижимости"""
    
    # Базовый queryset с предзагрузкой связанных объектов
    properties = Property.objects.select_related('building').prefetch_related('building__properties')
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(display_address__icontains=search_query) |
            Q(building__name__icontains=search_query) |
            Q(agent_name__icontains=search_query) |
            Q(broker_name__icontains=search_query)
        )
    
    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Фильтрация по количеству спален
    bedrooms = request.GET.get('bedrooms')
    if bedrooms:
        try:
            properties = properties.filter(bedrooms=int(bedrooms))
        except ValueError:
            pass
    
    # Фильтрация по типу (продажа/аренда)
    price_duration = request.GET.get('price_duration')
    if price_duration in ['sell', 'rent']:
        properties = properties.filter(price_duration=price_duration)
    
    # Фильтрация по району
    area = request.GET.get('area')
    if area:
        properties = properties.filter(building__area__icontains=area)
    
    # Фильтрация по зданию
    building_name = request.GET.get('building')
    if building_name:
        properties = properties.filter(building__name__icontains=building_name)
    
    # Фильтрация по ROI
    min_roi = request.GET.get('min_roi')
    max_roi = request.GET.get('max_roi')
    if min_roi:
        try:
            properties = properties.filter(roi__gte=float(min_roi))
        except ValueError:
            pass
    if max_roi:
        try:
            properties = properties.filter(roi__lte=float(max_roi))
        except ValueError:
            pass
    
    # Сортировка
    sort_by = request.GET.get('sort', 'created_at')
    sort_order = request.GET.get('order', 'desc')
    
    # Определяем доступные поля для сортировки
    sortable_fields = {
        'price': 'price',
        'bedrooms': 'bedrooms',
        'area': 'area_sqm',
        'roi': 'roi',
        'days_on_market': 'days_on_market',
        'created_at': 'created_at',
        'building': 'building__name',
        'area_name': 'building__area'
    }
    
    if sort_by in sortable_fields:
        order_prefix = '-' if sort_order == 'desc' else ''
        properties = properties.order_by(f'{order_prefix}{sortable_fields[sort_by]}')
    
    # Пагинация
    paginator = Paginator(properties, getattr(settings, 'PAGINATION_PER_PAGE', 50))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем список разрешенных районов
    available_areas = sorted(AREAS_WITH_PROPERTY.keys())
    
    buildings = Building.objects.values_list('name', flat=True).distinct().order_by('name')
    buildings = [building for building in buildings if building]  # Убираем пустые значения
    
    bedroom_choices = Property.objects.values_list('bedrooms', flat=True).distinct().order_by('bedrooms')
    bedroom_choices = [br for br in bedroom_choices if br is not None]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'available_areas': available_areas,
        'buildings': buildings,
        'bedroom_choices': bedroom_choices,
        'current_filters': {
            'min_price': min_price,
            'max_price': max_price,
            'bedrooms': bedrooms,
            'price_duration': price_duration,
            'area': area,
            'building': building_name,
            'min_roi': min_roi,
            'max_roi': max_roi,
            'sort': sort_by,
            'order': sort_order,
        },
        'total_properties': paginator.count,
    }
    
    return render(request, 'properties/property_list_simple.html', context)


def property_analytics(request):
    """Страница с аналитикой"""
    
    # Аналитика по районам
    area_stats = Building.objects.values('area').annotate(
        total_buildings=Count('id'),
        total_properties=Count('properties'),
        avg_sale_price=Avg(
            Case(
                When(properties__price_duration='sell', then='properties__price'),
                output_field=FloatField()
            )
        ),
        avg_rent_price=Avg(
            Case(
                When(properties__price_duration='rent', then='properties__price'),
                output_field=FloatField()
            )
        ),
        sale_count=Count(
            Case(
                When(properties__price_duration='sell', then=1)
            )
        ),
        rent_count=Count(
            Case(
                When(properties__price_duration='rent', then=1)
            )
        ),
        avg_roi=Avg('properties__roi')
    ).exclude(area__isnull=True).order_by('area')
    
    # Общая статистика
    total_properties = Property.objects.count()
    total_buildings = Building.objects.count()
    avg_price_sale = Property.objects.filter(
        price_duration='sell', 
        price__isnull=False
    ).aggregate(avg=Avg('price'))['avg'] or 0
    avg_price_rent = Property.objects.filter(
        price_duration='rent', 
        price__isnull=False
    ).aggregate(avg=Avg('price'))['avg'] or 0
    
    context = {
        'area_stats': area_stats,
        'total_properties': total_properties,
        'total_buildings': total_buildings,
        'avg_price_sale': avg_price_sale,
        'avg_price_rent': avg_price_rent,
    }
    
    return render(request, 'properties/analytics.html', context)


def building_detail(request, building_id):
    """Детальная информация о здании"""
    try:
        building = Building.objects.get(id=building_id)
        properties = building.properties.all().order_by('-created_at')
        
        # Статистика здания
        stats = {
            'total_properties': properties.count(),
            'sale_count': properties.filter(price_duration='sell').count(),
            'rent_count': properties.filter(price_duration='rent').count(),
            'avg_sale_price': building.avg_sale_price(),
            'avg_rent_price': building.avg_rent_price(),
            'avg_roi': building.avg_roi(),
        }
        
        context = {
            'building': building,
            'properties': properties,
            'stats': stats,
        }
        
        return render(request, 'properties/building_detail.html', context)
    
    except Building.DoesNotExist:
        return render(request, '404.html', status=404)


def api_buildings(request):
    """API для получения списка зданий (для AJAX)"""
    term = request.GET.get('term', '')
    buildings = Building.objects.filter(name__icontains=term)[:10]
    
    results = [
        {
            'id': building.id,
            'text': building.name,
            'address': building.address
        }
        for building in buildings
    ]
    
    return JsonResponse({'results': results})


def api_areas(request):
    """API для получения списка районов (для AJAX)"""
    term = request.GET.get('term', '')
    areas = Building.objects.filter(
        area__icontains=term
    ).values_list('area', flat=True).distinct()[:10]
    
    results = [
        {'id': area, 'text': area}
        for area in areas if area
    ]
    
    return JsonResponse({'results': results})


# ========================================
# MVP Views for Parser Service
# ========================================

def health_check(request):
    """Health check endpoint for Docker and monitoring."""
    try:
        # Check database connectivity
        property_count = Property.objects.count()
        
        # Check if recent data exists (last 24 hours)
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        recent_count = Property.objects.filter(created_at__gte=yesterday).count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'database': 'connected',
            'total_properties': property_count,
            'recent_properties_24h': recent_count,
            'service': 'parser'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'error': str(e),
            'service': 'parser'
        }, status=500)


def index(request):
    """Simple index page for parser service."""
    try:
        property_count = Property.objects.count()
        building_count = Building.objects.count()
        
        # Recent statistics
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        recent_count = Property.objects.filter(created_at__gte=yesterday).count()
        
        context = {
            'service_name': 'PropertyFinder Parser',
            'total_properties': property_count,
            'total_buildings': building_count,
            'recent_properties': recent_count,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render(request, 'properties/index.html', context)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Service error',
            'message': str(e)
        }, status=500)


def properties_list(request):
    """API endpoint to list properties for main service."""
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        # Get properties
        properties = Property.objects.all().order_by('-created_at')[offset:offset+limit]
        
        # Convert to JSON format
        properties_data = []
        for prop in properties:
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': float(prop.price) if prop.price else 0,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'display_address': prop.display_address,
                'property_type': prop.property_type,
                'created_at': prop.created_at.isoformat() if prop.created_at else None,
            })
        
        return JsonResponse({
            'count': len(properties_data),
            'results': properties_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch properties',
            'message': str(e)
        }, status=500)


def export_view(request):
    """Simple web interface to trigger export."""
    if request.method == 'POST':
        # In a real implementation, this would trigger the export command
        return JsonResponse({
            'status': 'export_triggered',
            'message': 'Export to shared data initiated'
        })
    
    return render(request, 'properties/export.html')


def stats_view(request):
    """Statistics API endpoint."""
    try:
        stats = {
            'total_properties': Property.objects.count(),
            'total_buildings': Building.objects.count(),
            'by_property_type': {},
            'by_bedrooms': {},
            'recent_24h': Property.objects.filter(
                created_at__gte=datetime.datetime.now() - datetime.timedelta(days=1)
            ).count(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Properties by type
        for prop_type in Property.objects.values_list('property_type', flat=True).distinct():
            if prop_type:
                stats['by_property_type'][prop_type] = Property.objects.filter(
                    property_type=prop_type
                ).count()
        
        # Properties by bedrooms
        for bedrooms in Property.objects.values_list('bedrooms', flat=True).distinct():
            if bedrooms is not None:
                stats['by_bedrooms'][str(bedrooms)] = Property.objects.filter(
                    bedrooms=bedrooms
                ).count()
        
        return JsonResponse(stats)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to generate stats',
            'message': str(e)
        }, status=500) 
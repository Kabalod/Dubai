import strawberry
from strawberry_django import auto
from typing import List, Optional
from django.db.models import Avg, Count, Sum, Min, Max
from .models import Area, Building, Project, MergedTransaction, MergedRentalTransaction


@strawberry.django.type(Area)
class AreaType:
    id: auto
    name_en: auto
    name_ar: auto
    area_idx: auto


@strawberry.django.type(Building)
class BuildingType:
    id: auto
    english_name: auto
    arabic_name: auto
    latitude: auto
    longitude: auto
    area: AreaType
    project: auto


@strawberry.django.type(Project)
class ProjectType:
    id: auto
    english_name: auto
    arabic_name: auto
    worth: auto
    total_area: auto
    total_units: auto
    developer: auto


@strawberry.django.type(MergedTransaction)
class TransactionType:
    id: auto
    contract_amount: auto
    contract_date: auto
    building: BuildingType
    project: ProjectType
    area: AreaType
    number_of_rooms: auto
    sqm: auto
    meter_sale_price: auto


@strawberry.django.type(MergedRentalTransaction)
class RentalTransactionType:
    id: auto
    annual_amount: auto
    contract_start_date: auto
    building: BuildingType
    project: ProjectType
    area: AreaType
    number_of_rooms: auto
    sqm: auto


@strawberry.type
class AreaAnalytics:
    area: AreaType
    total_transactions: int
    total_rental_transactions: int
    avg_price: float
    avg_rent: float
    avg_sqm: float
    building_count: int
    project_count: int


@strawberry.type
class BuildingAnalytics:
    building: BuildingType
    total_transactions: int
    total_rental_transactions: int
    avg_price: float
    avg_rent: float
    avg_sqm: float
    days_on_market: int
    roi: float


@strawberry.type
class ProjectAnalytics:
    project: ProjectType
    total_transactions: int
    total_rental_transactions: int
    avg_price: float
    avg_rent: float
    avg_sqm: float
    building_count: int
    occupancy_rate: float


@strawberry.type
class MarketOverview:
    total_areas: int
    total_buildings: int
    total_projects: int
    total_transactions: int
    total_rental_transactions: int
    avg_price: float
    avg_rent: float
    avg_sqm: float
    price_trend: str
    rent_trend: str


@strawberry.type
class Query:
    @strawberry.field
    def areas(self, info) -> List[AreaType]:
        return Area.objects.all()
    
    @strawberry.field
    def buildings(self, info) -> List[BuildingType]:
        return Building.objects.select_related('area', 'project').all()
    
    @strawberry.field
    def projects(self, info) -> List[ProjectType]:
        return Project.objects.all()
    
    @strawberry.field
    def transactions(self, info) -> List[TransactionType]:
        return MergedTransaction.objects.select_related('building', 'project', 'area').all()
    
    @strawberry.field
    def rental_transactions(self, info) -> List[RentalTransactionType]:
        return MergedRentalTransaction.objects.select_related('building', 'project', 'area').all()
    
    @strawberry.field
    def area_analytics(self, info, area_id: int) -> AreaAnalytics:
        area = Area.objects.get(id=area_id)
        
        # Аналитика по сделкам
        transactions = MergedTransaction.objects.filter(building__area=area)
        rental_transactions = MergedRentalTransaction.objects.filter(building__area=area)
        
        # Агрегированные метрики
        transaction_stats = transactions.aggregate(
            total=Count('id'),
            avg_price=Avg('contract_amount'),
            avg_sqm=Avg('sqm')
        )
        
        rental_stats = rental_transactions.aggregate(
            total=Count('id'),
            avg_rent=Avg('annual_amount')
        )
        
        building_count = Building.objects.filter(area=area).count()
        project_count = Project.objects.filter(buildings__area=area).distinct().count()
        
        return AreaAnalytics(
            area=area,
            total_transactions=transaction_stats['total'] or 0,
            total_rental_transactions=rental_stats['total'] or 0,
            avg_price=float(transaction_stats['avg_price'] or 0),
            avg_rent=float(rental_stats['avg_rent'] or 0),
            avg_sqm=float(transaction_stats['avg_sqm'] or 0),
            building_count=building_count,
            project_count=project_count
        )
    
    @strawberry.field
    def building_analytics(self, info, building_id: int) -> BuildingAnalytics:
        building = Building.objects.get(id=building_id)
        
        # Аналитика по сделкам
        transactions = MergedTransaction.objects.filter(building=building)
        rental_transactions = MergedRentalTransaction.objects.filter(building=building)
        
        # Агрегированные метрики
        transaction_stats = transactions.aggregate(
            total=Count('id'),
            avg_price=Avg('contract_amount'),
            avg_sqm=Avg('sqm'),
            avg_days=Avg('days_on_market')
        )
        
        rental_stats = rental_transactions.aggregate(
            total=Count('id'),
            avg_rent=Avg('annual_amount')
        )
        
        # Расчет ROI (упрощенный)
        avg_price = transaction_stats['avg_price'] or 0
        avg_rent = rental_stats['avg_rent'] or 0
        roi = (avg_rent * 12 / avg_price * 100) if avg_price > 0 else 0
        
        return BuildingAnalytics(
            building=building,
            total_transactions=transaction_stats['total'] or 0,
            total_rental_transactions=rental_stats['total'] or 0,
            avg_price=float(avg_price),
            avg_rent=float(avg_rent),
            avg_sqm=float(transaction_stats['avg_sqm'] or 0),
            days_on_market=int(transaction_stats['avg_days'] or 0),
            roi=float(roi)
        )

    @strawberry.field
    def project_analytics(self, info, project_id: int) -> ProjectAnalytics:
        project = Project.objects.get(id=project_id)
        
        # Аналитика по сделкам
        transactions = MergedTransaction.objects.filter(building__project=project)
        rental_transactions = MergedRentalTransaction.objects.filter(building__project=project)
        
        # Агрегированные метрики
        transaction_stats = transactions.aggregate(
            total=Count('id'),
            avg_price=Avg('contract_amount'),
            avg_sqm=Avg('sqm')
        )
        
        rental_stats = rental_transactions.aggregate(
            total=Count('id'),
            avg_rent=Avg('annual_amount')
        )
        
        building_count = Building.objects.filter(project=project).count()
        total_units = project.total_units or 0
        occupancy_rate = (transaction_stats['total'] / total_units * 100) if total_units > 0 else 0
        
        return ProjectAnalytics(
            project=project,
            total_transactions=transaction_stats['total'] or 0,
            total_rental_transactions=rental_stats['total'] or 0,
            avg_price=float(transaction_stats['avg_price'] or 0),
            avg_rent=float(rental_stats['avg_rent'] or 0),
            avg_sqm=float(transaction_stats['avg_sqm'] or 0),
            building_count=building_count,
            occupancy_rate=float(occupancy_rate)
        )

    @strawberry.field
    def market_overview(self, info) -> MarketOverview:
        # Общая статистика рынка
        total_areas = Area.objects.count()
        total_buildings = Building.objects.count()
        total_projects = Project.objects.count()
        
        # Статистика по сделкам
        transactions = MergedTransaction.objects.all()
        rental_transactions = MergedRentalTransaction.objects.all()
        
        transaction_stats = transactions.aggregate(
            total=Count('id'),
            avg_price=Avg('contract_amount'),
            avg_sqm=Avg('sqm')
        )
        
        rental_stats = rental_transactions.aggregate(
            total=Count('id'),
            avg_rent=Avg('annual_amount')
        )
        
        # Упрощенные тренды (можно заменить на реальную логику)
        price_trend = "stable"  # placeholder
        rent_trend = "stable"   # placeholder
        
        return MarketOverview(
            total_areas=total_areas,
            total_buildings=total_buildings,
            total_projects=total_projects,
            total_transactions=transaction_stats['total'] or 0,
            total_rental_transactions=rental_stats['total'] or 0,
            avg_price=float(transaction_stats['avg_price'] or 0),
            avg_rent=float(rental_stats['avg_rent'] or 0),
            avg_sqm=float(transaction_stats['avg_sqm'] or 0),
            price_trend=price_trend,
            rent_trend=rent_trend
        )


schema = strawberry.Schema(query=Query)

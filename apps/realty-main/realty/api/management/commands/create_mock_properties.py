#!/usr/bin/env python3
"""
Management команда для создания mock данных недвижимости (заглушка парсера)
для демонстрации функционала без реального парсинга PropertyFinder

Использование:
    python manage.py create_mock_properties
    python manage.py create_mock_properties --clean  # очистить перед созданием
    python manage.py create_mock_properties --count=100  # количество объявлений
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

try:
    from realty.pfimport.models import Area, Building, PFListSale, PFListRent
    from realty.main.models import Area as MainArea
except ImportError:
    # Fallback если модели недоступны
    Area = Building = PFListSale = PFListRent = MainArea = None


class Command(BaseCommand):
    help = 'Создает mock данные недвижимости для демонстрации MVP без парсера PropertyFinder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Очистить существующие mock данные перед созданием новых'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Количество объявлений для создания (по умолчанию: 50)'
        )
        parser.add_argument(
            '--areas-count',
            type=int,
            default=10,
            help='Количество районов для создания (по умолчанию: 10)'
        )
        parser.add_argument(
            '--buildings-count',
            type=int,
            default=20,
            help='Количество зданий для создания (по умолчанию: 20)'
        )

    def handle(self, *args, **options):
        if not all([Area, Building, PFListSale, PFListRent]):
            self.stdout.write(
                self.style.ERROR('❌ Модели недвижимости недоступны. Убедитесь что pfimport установлен.')
            )
            return

        clean_data = options['clean']
        properties_count = options['count']
        areas_count = options['areas_count']
        buildings_count = options['buildings_count']

        self.stdout.write(self.style.SUCCESS('🏠 Создание mock данных недвижимости для MVP...'))

        if clean_data:
            self.clean_mock_data()

        # Создаем районы (Areas)
        areas = self.create_mock_areas(areas_count)
        
        # Создаем здания (Buildings)
        buildings = self.create_mock_buildings(buildings_count, areas)
        
        # Создаем объявления продажи (PFListSale)
        sale_count = int(properties_count * 0.6)  # 60% продажа
        self.create_mock_sale_properties(sale_count, buildings, areas)
        
        # Создаем объявления аренды (PFListRent)
        rent_count = properties_count - sale_count  # 40% аренда
        self.create_mock_rent_properties(rent_count, buildings, areas)

        self.stdout.write(self.style.SUCCESS('✅ Mock данные недвижимости успешно созданы!'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('🔗 Для тестирования:'))
        self.stdout.write(self.style.SUCCESS('  🏢 Продажа: /pfimport/sale/'))
        self.stdout.write(self.style.SUCCESS('  🏡 Аренда: /pfimport/rent/'))
        self.stdout.write(self.style.SUCCESS('  📍 Здания: /pfimport/api/buildings/'))
        self.stdout.write(self.style.SUCCESS('  🗺️ Карта: /pfimport/map/'))

    def clean_mock_data(self):
        """Очищает mock данные недвижимости"""
        self.stdout.write(self.style.WARNING('🧹 Очистка существующих mock данных недвижимости...'))
        
        # Удаляем mock объявления
        PFListSale.objects.filter(listing_id__startswith='mock_sale_').delete()
        PFListRent.objects.filter(listing_id__startswith='mock_rent_').delete()
        
        # Удаляем mock здания и районы
        Building.objects.filter(building_name__startswith='Mock Building').delete()
        Area.objects.filter(area_name__startswith='Mock Area').delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Очистка завершена'))

    def create_mock_areas(self, count):
        """Создает тестовые районы Дубая"""
        self.stdout.write(self.style.SUCCESS(f'📍 Создание {count} районов Дубая...'))
        
        dubai_areas = [
            'Dubai Marina', 'Downtown Dubai', 'Jumeirah Beach Residence (JBR)',
            'Business Bay', 'Dubai Hills Estate', 'Arabian Ranches',
            'Jumeirah Village Circle (JVC)', 'Dubai South', 'Al Barsha',
            'Jumeirah Lakes Towers (JLT)', 'The Greens', 'Emirates Hills',
            'Palm Jumeirah', 'Bluewaters Island', 'Dubai Healthcare City',
            'DIFC (Dubai International Financial Centre)', 'City Walk',
            'Mirdif', 'Dubai Silicon Oasis', 'Jumeirah'
        ]
        
        areas = []
        
        for i in range(min(count, len(dubai_areas))):
            area_name = dubai_areas[i]
            
            area, created = Area.objects.get_or_create(
                area_name=area_name,
                defaults={
                    'area_name': area_name,
                }
            )
            
            areas.append(area)
            
            status = "создан" if created else "уже существует"
            self.stdout.write(f'  📍 {area.area_name} - {status}')

        # Создаем дополнительные mock районы если нужно
        for i in range(len(dubai_areas), count):
            area_name = f'Mock Area {i+1}'
            
            area, created = Area.objects.get_or_create(
                area_name=area_name,
                defaults={
                    'area_name': area_name,
                }
            )
            
            areas.append(area)
            
            if created:
                self.stdout.write(f'  📍 {area.area_name} - создан')

        return areas

    def create_mock_buildings(self, count, areas):
        """Создает тестовые здания"""
        self.stdout.write(self.style.SUCCESS(f'🏢 Создание {count} зданий...'))
        
        building_types = [
            'Tower', 'Residence', 'Plaza', 'Heights', 'Park', 'Gardens',
            'Marina', 'Bay', 'Square', 'Court', 'Villas', 'Apartments'
        ]
        
        buildings = []
        
        for i in range(count):
            area = random.choice(areas)
            building_type = random.choice(building_types)
            building_name = f'Mock Building {i+1} {building_type}'
            
            # Генерируем координаты в пределах Дубая
            latitude = random.uniform(25.0500, 25.3000)  # Дубай широта
            longitude = random.uniform(55.0000, 55.4000)  # Дубай долгота
            
            building, created = Building.objects.get_or_create(
                building_name=building_name,
                defaults={
                    'building_name': building_name,
                    'area': area,
                    'latitude': latitude,
                    'longitude': longitude,
                }
            )
            
            buildings.append(building)
            
            if created:
                self.stdout.write(f'  🏢 {building.building_name} в {area.area_name} - создан')

        return buildings

    def create_mock_sale_properties(self, count, buildings, areas):
        """Создает объявления продажи"""
        self.stdout.write(self.style.SUCCESS(f'🏠 Создание {count} объявлений продажи...'))
        
        property_types = ['Apartment', 'Villa', 'Townhouse', 'Penthouse']
        bedrooms_options = ['studio', '1', '2', '3', '4', '5']
        bathrooms_options = ['1', '2', '3', '4', '5']
        
        for i in range(count):
            building = random.choice(buildings)
            area = building.area or random.choice(areas)
            property_type = random.choice(property_types)
            bedrooms = random.choice(bedrooms_options)
            bathrooms = random.choice(bathrooms_options)
            
            # Генерируем реалистичные цены в AED
            if bedrooms == 'studio':
                price = Decimal(random.uniform(400000, 800000))
                area_size = random.uniform(450, 650)
            elif bedrooms == '1':
                price = Decimal(random.uniform(700000, 1500000))
                area_size = random.uniform(650, 900)
            elif bedrooms == '2':
                price = Decimal(random.uniform(1200000, 2500000))
                area_size = random.uniform(900, 1300)
            elif bedrooms == '3':
                price = Decimal(random.uniform(2000000, 4000000))
                area_size = random.uniform(1300, 1800)
            else:  # 4+ bedrooms
                price = Decimal(random.uniform(3500000, 8000000))
                area_size = random.uniform(1800, 3000)
            
            # Случайная дата добавления в последние 60 дней
            days_ago = random.randint(0, 60)
            added_date = timezone.now() - timedelta(days=days_ago)
            
            listing = PFListSale.objects.create(
                listing_id=f'mock_sale_{i+1}',
                title=f'{bedrooms.title()} BR {property_type} for Sale in {area.area_name}',
                display_address=f'{building.building_name}, {area.area_name}',
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                listing_type='Residential for Sale',
                price=price,
                price_currency='AED',
                price_duration='sell',
                building=building,
                area=area,
                latitude=building.latitude + random.uniform(-0.001, 0.001),
                longitude=building.longitude + random.uniform(-0.001, 0.001),
                numeric_area=area_size,
                size_min=f'{int(area_size)} sqft',
                broker='Mock Real Estate Agency',
                agent=f'Agent {random.randint(1, 50)}',
                agent_phone=f'+971 50 {random.randint(1000000, 9999999)}',
                verified=random.choice([True, False]),
                furnishing=random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished']),
                added_on=added_date,
                description=f'Beautiful {bedrooms} bedroom {property_type.lower()} with stunning views. Prime location in {area.area_name}.',
                url=f'https://mock-propertyfinder.com/sale/{i+1}'
            )
            
            if i < 5:  # Показываем первые 5 для примера
                self.stdout.write(
                    f'  🏠 {listing.title} - {listing.price:,.0f} AED'
                )

    def create_mock_rent_properties(self, count, buildings, areas):
        """Создает объявления аренды"""
        self.stdout.write(self.style.SUCCESS(f'🏡 Создание {count} объявлений аренды...'))
        
        property_types = ['Apartment', 'Villa', 'Townhouse', 'Studio']
        bedrooms_options = ['studio', '1', '2', '3', '4']
        bathrooms_options = ['1', '2', '3', '4']
        
        for i in range(count):
            building = random.choice(buildings)
            area = building.area or random.choice(areas)
            property_type = random.choice(property_types)
            bedrooms = random.choice(bedrooms_options)
            bathrooms = random.choice(bathrooms_options)
            
            # Генерируем реалистичные цены аренды в AED (годовые)
            if bedrooms == 'studio':
                price = Decimal(random.uniform(35000, 60000))
                area_size = random.uniform(450, 650)
            elif bedrooms == '1':
                price = Decimal(random.uniform(55000, 95000))
                area_size = random.uniform(650, 900)
            elif bedrooms == '2':
                price = Decimal(random.uniform(85000, 150000))
                area_size = random.uniform(900, 1300)
            elif bedrooms == '3':
                price = Decimal(random.uniform(130000, 250000))
                area_size = random.uniform(1300, 1800)
            else:  # 4+ bedrooms
                price = Decimal(random.uniform(200000, 400000))
                area_size = random.uniform(1800, 2500)
            
            # Случайная дата добавления в последние 30 дней
            days_ago = random.randint(0, 30)
            added_date = timezone.now() - timedelta(days=days_ago)
            
            listing = PFListRent.objects.create(
                listing_id=f'mock_rent_{i+1}',
                title=f'{bedrooms.title()} BR {property_type} for Rent in {area.area_name}',
                display_address=f'{building.building_name}, {area.area_name}',
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                listing_type='Residential for Rent',
                price=price,
                price_currency='AED',
                price_duration='rent',
                building=building,
                area=area,
                latitude=building.latitude + random.uniform(-0.001, 0.001),
                longitude=building.longitude + random.uniform(-0.001, 0.001),
                numeric_area=area_size,
                size_min=f'{int(area_size)} sqft',
                broker='Mock Property Management',
                agent=f'Rental Agent {random.randint(1, 30)}',
                agent_phone=f'+971 50 {random.randint(1000000, 9999999)}',
                verified=random.choice([True, False]),
                furnishing=random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished']),
                added_on=added_date,
                description=f'Spacious {bedrooms} bedroom {property_type.lower()} available for rent. Excellent amenities in {area.area_name}.',
                url=f'https://mock-propertyfinder.com/rent/{i+1}'
            )
            
            if i < 5:  # Показываем первые 5 для примера
                self.stdout.write(
                    f'  🏡 {listing.title} - {listing.price:,.0f} AED/year'
                )

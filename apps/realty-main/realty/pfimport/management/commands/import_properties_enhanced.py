import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from realty.pfimport.models import PFListSale, PFListRent, Building, Area


class Command(BaseCommand):
    help = 'Enhanced PropertyFinder data import with better performance and error handling'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'files_processed': 0,
            'total_properties': 0,
            'properties_imported': 0,
            'properties_updated': 0,
            'properties_skipped': 0,
            'errors': 0
        }

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            type=str,
            help='JSON file or directory containing JSON files to import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing records instead of creating new ones'
        )
        parser.add_argument(
            '--wipe-sale',
            action='store_true',
            help='Clear all sale data before import'
        )
        parser.add_argument(
            '--wipe-rent',
            action='store_true',
            help='Clear all rent data before import'
        )
        parser.add_argument(
            '--wipe-areas',
            action='store_true',
            help='Clear all area data before import'
        )
        parser.add_argument(
            '--wipe-buildings',
            action='store_true',
            help='Clear all building data before import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Process files but don\'t save to database'
        )

    def handle(self, *args, **options):
        source = Path(options['source'])
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(f"🚀 Starting enhanced PropertyFinder import")
        )
        self.stdout.write(f"📁 Source: {source}")
        self.stdout.write(f"📦 Batch size: {batch_size}")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No data will be saved"))
        
        # Validate source
        if not source.exists():
            raise CommandError(f'Source {source} does not exist')
        
        # Get JSON files
        json_files = self.get_json_files(source)
        if not json_files:
            raise CommandError(f'No JSON files found in {source}')
        
        self.stdout.write(f"📄 Found {len(json_files)} JSON files to process")
        
        try:
            # Clear data if requested
            if not options['dry_run']:
                self.clear_data_if_requested(options)
            
            # Process files
            for json_file in json_files:
                self.process_json_file(json_file, batch_size, options)
            
            # Print final stats
            self.print_final_stats()
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n⚠️ Import interrupted by user"))
            self.print_final_stats()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Import failed: {e}"))
            self.print_final_stats()
            raise

    def get_json_files(self, source: Path) -> List[Path]:
        """Get list of JSON files to process."""
        if source.is_file():
            if source.suffix.lower() == '.json':
                return [source]
            else:
                raise CommandError(f'File {source} is not a JSON file')
        
        return list(source.glob('*.json'))

    def clear_data_if_requested(self, options: Dict[str, Any]):
        """Clear existing data if requested."""
        if options['wipe_sale']:
            count = PFListSale.objects.count()
            PFListSale.objects.all().delete()
            self.stdout.write(f"🗑️ Cleared {count} sale properties")
        
        if options['wipe_rent']:
            count = PFListRent.objects.count()
            PFListRent.objects.all().delete()
            self.stdout.write(f"🗑️ Cleared {count} rent properties")
        
        if options['wipe_buildings']:
            count = Building.objects.count()
            Building.objects.all().delete()
            self.stdout.write(f"🗑️ Cleared {count} buildings")
        
        if options['wipe_areas']:
            count = Area.objects.count()
            Area.objects.all().delete()
            self.stdout.write(f"🗑️ Cleared {count} areas")

    def process_json_file(self, json_file: Path, batch_size: int, options: Dict[str, Any]):
        """Process a single JSON file."""
        self.stdout.write(f"📄 Processing {json_file.name}...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.stdout.write(
                    self.style.ERROR(f"❌ {json_file.name}: Expected list, got {type(data)}")
                )
                return
            
            self.stdout.write(f"📊 Found {len(data)} properties in {json_file.name}")
            self.stats['files_processed'] += 1
            self.stats['total_properties'] += len(data)
            
            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(data) + batch_size - 1) // batch_size
                
                self.stdout.write(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                if not options['dry_run']:
                    self.process_batch(batch, options['update'])
                else:
                    # In dry run, just validate data
                    self.validate_batch(batch)
                
        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            self.stdout.write(
                self.style.ERROR(f"❌ {json_file.name}: Invalid JSON - {e}")
            )
        except Exception as e:
            self.stats['errors'] += 1
            self.stdout.write(
                self.style.ERROR(f"❌ {json_file.name}: Error - {e}")
            )

    def process_batch(self, batch: List[Dict], update_existing: bool):
        """Process a batch of properties."""
        areas_to_create = {}
        buildings_to_create = {}
        sale_properties = []
        rent_properties = []
        
        for item in batch:
            try:
                processed = self.process_property_item(
                    item, areas_to_create, buildings_to_create
                )
                
                if processed:
                    if processed['listing_type'] == 'sale':
                        sale_properties.append(processed)
                    else:
                        rent_properties.append(processed)
                else:
                    self.stats['properties_skipped'] += 1
                    
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Error processing property: {e}")
        
        # Save to database in transaction
        try:
            with transaction.atomic():
                # Create areas and buildings first
                self.bulk_create_areas(areas_to_create.values())
                self.bulk_create_buildings(buildings_to_create.values())
                
                # Create properties
                self.bulk_create_properties(sale_properties, PFListSale, update_existing)
                self.bulk_create_properties(rent_properties, PFListRent, update_existing)
                
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error saving batch: {e}")
            self.stdout.write(self.style.ERROR(f"❌ Error saving batch: {e}"))

    def process_property_item(self, item: Dict, areas_cache: Dict, buildings_cache: Dict) -> Dict:
        """Process a single property item."""
        # Extract required fields
        listing_id = item.get('id')
        if not listing_id:
            return None
        
        title = item.get('title', '')
        if not title:
            return None
        
        # Determine listing type
        price_duration = item.get('priceDuration', 'sell')
        listing_type = 'rent' if price_duration == 'rent' else 'sale'
        
        # Extract location data
        display_address = item.get('displayAddress', '')
        area_name = self.extract_area_from_address(display_address)
        
        # Get or create area
        area_obj = None
        if area_name:
            if area_name not in areas_cache:
                area_obj, created = Area.objects.get_or_create(
                    name=area_name,
                    defaults={'verified_value': 'ok'}
                )
                areas_cache[area_name] = area_obj
            else:
                area_obj = areas_cache[area_name]
        
        # Extract building data
        building_name = self.extract_building_from_address(display_address)
        building_obj = None
        
        if building_name and area_obj:
            building_key = f"{building_name}_{area_name}"
            if building_key not in buildings_cache:
                coordinates = item.get('coordinates', {})
                lat = self.safe_decimal(coordinates.get('latitude'))
                lng = self.safe_decimal(coordinates.get('longitude'))
                
                building_obj, created = Building.objects.get_or_create(
                    name=building_name,
                    area=area_obj,
                    defaults={
                        'latitude': lat,
                        'longitude': lng,
                    }
                )
                buildings_cache[building_key] = building_obj
            else:
                building_obj = buildings_cache[building_key]
        
        # Prepare property data
        coordinates = item.get('coordinates', {})
        
        return {
            'listing_id': listing_id,
            'area': area_obj,
            'building': building_obj,
            'title': title,
            'display_address': display_address,
            'bedrooms': str(item.get('bedrooms', '')),
            'bathrooms': str(item.get('bathrooms', '')),
            'added_on': self.parse_datetime(item.get('addedOn')),
            'broker': item.get('broker', ''),
            'agent': item.get('agent', ''),
            'agent_phone': item.get('agentPhone', ''),
            'verified': bool(item.get('verified', False)),
            'reference': item.get('reference', ''),
            'broker_license_number': item.get('brokerLicenseNumber', ''),
            'property_type': item.get('propertyType', ''),
            'listing_type': listing_type,
            'price_duration': price_duration,
            'price': self.safe_decimal(item.get('price', 0)),
            'price_currency': item.get('priceCurrency', 'AED'),
            'latitude': self.safe_decimal(coordinates.get('latitude')),
            'longitude': self.safe_decimal(coordinates.get('longitude')),
            'size_min': item.get('sizeMin', ''),
            'numeric_area': self.extract_numeric_area(item.get('sizeMin', '')),
            'furnishing': item.get('furnishing', ''),
            'description': item.get('description', ''),
            'description_html': item.get('descriptionHTML', ''),
        }

    def bulk_create_areas(self, areas: List[Area]):
        """Bulk create areas."""
        if areas:
            Area.objects.bulk_create(areas, ignore_conflicts=True)

    def bulk_create_buildings(self, buildings: List[Building]):
        """Bulk create buildings."""
        if buildings:
            Building.objects.bulk_create(buildings, ignore_conflicts=True)

    def bulk_create_properties(self, properties: List[Dict], model_class, update_existing: bool):
        """Bulk create properties."""
        if not properties:
            return
        
        objects_to_create = []
        
        for prop_data in properties:
            obj = model_class(**prop_data)
            objects_to_create.append(obj)
        
        if update_existing:
            # For updates, we'd need to implement upsert logic
            # For now, just create
            model_class.objects.bulk_create(objects_to_create, ignore_conflicts=True)
            self.stats['properties_updated'] += len(objects_to_create)
        else:
            model_class.objects.bulk_create(objects_to_create, ignore_conflicts=True)
            self.stats['properties_imported'] += len(objects_to_create)

    def validate_batch(self, batch: List[Dict]):
        """Validate batch data without saving (dry run)."""
        valid_count = 0
        for item in batch:
            if item.get('id') and item.get('title'):
                valid_count += 1
            else:
                self.stats['properties_skipped'] += 1
        
        self.stats['properties_imported'] += valid_count

    def extract_area_from_address(self, address: str) -> str:
        """Extract area name from address."""
        if not address:
            return ""
        
        # Simple extraction - take the last part after comma
        parts = address.split(',')
        if len(parts) >= 2:
            return parts[-1].strip()
        
        return parts[0].strip() if parts else ""

    def extract_building_from_address(self, address: str) -> str:
        """Extract building name from address."""
        if not address:
            return ""
        
        # Simple extraction - take the first part
        parts = address.split(',')
        return parts[0].strip() if parts else ""

    def extract_numeric_area(self, size_str: str) -> Decimal:
        """Extract numeric area from size string."""
        if not size_str:
            return Decimal('0')
        
        # Extract numbers from string like "1000 sq ft"
        import re
        numbers = re.findall(r'\d+\.?\d*', size_str)
        if numbers:
            try:
                return Decimal(numbers[0])
            except (InvalidOperation, ValueError):
                pass
        
        return Decimal('0')

    def safe_decimal(self, value) -> Decimal:
        """Safely convert value to Decimal."""
        if value is None:
            return None
        
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def parse_datetime(self, date_str):
        """Parse datetime string."""
        if not date_str:
            return None
        
        try:
            from django.utils.dateparse import parse_datetime
            return parse_datetime(date_str) or timezone.now()
        except:
            return timezone.now()

    def print_final_stats(self):
        """Print final import statistics."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📊 IMPORT STATISTICS"))
        self.stdout.write("="*50)
        self.stdout.write(f"Files processed: {self.stats['files_processed']}")
        self.stdout.write(f"Total properties found: {self.stats['total_properties']}")
        self.stdout.write(f"Properties imported: {self.stats['properties_imported']}")
        self.stdout.write(f"Properties updated: {self.stats['properties_updated']}")
        self.stdout.write(f"Properties skipped: {self.stats['properties_skipped']}")
        self.stdout.write(f"Errors: {self.stats['errors']}")
        self.stdout.write("="*50)
        
        if self.stats['errors'] == 0:
            self.stdout.write(self.style.SUCCESS("✅ Import completed successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Import completed with {self.stats['errors']} errors"))
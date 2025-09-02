import os
import json
import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db.models import Q
from properties.models import Property


class Command(BaseCommand):
    help = "Export properties to shared data directory for main API consumption"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default="/shared-data",
            help="Output directory for exported JSON files"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of properties to export"
        )
        parser.add_argument(
            "--recent-days",
            type=int,
            default=None,
            help="Only export properties from last N days"
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        limit = options["limit"]
        recent_days = options["recent_days"]
        
        self.stdout.write(self.style.SUCCESS("🚀 Starting export to shared data..."))
        
        # Build querysets using single Property model
        sale_qs = Property.objects.filter(price_duration='sell').order_by('-created_at')
        rent_qs = Property.objects.filter(price_duration='rent').order_by('-created_at')
        
        # Filter by recent days if specified
        if recent_days:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=recent_days)
            sale_qs = sale_qs.filter(created_at__gte=cutoff_date)
            rent_qs = rent_qs.filter(created_at__gte=cutoff_date)
        
        # Apply limit
        if limit:
            sale_qs = sale_qs[:limit//2]  # Split limit between sale and rent
            rent_qs = rent_qs[:limit//2]
        
        # Export sales
        sales_data = []
        for prop in sale_qs:
            sales_data.append({
                'id': prop.id,
                'url': prop.url or '',
                'title': prop.title or '',
                'displayAddress': prop.display_address or '',
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'addedOn': prop.added_on.isoformat() if prop.added_on else None,
                'broker': prop.broker_name or '',
                'agent': prop.agent_name or '',
                'agentPhone': prop.agent_phone or '',
                'verified': prop.verified,
                'reference': prop.reference or '',
                'brokerLicenseNumber': prop.broker_license or '',
                'priceDuration': 'sell',
                'propertyType': prop.property_type or '',
                'price': float(prop.price) if prop.price else 0,
                'priceCurrency': prop.price_currency or 'AED',
                'coordinates': {
                    'latitude': float(prop.latitude) if prop.latitude else None,
                    'longitude': float(prop.longitude) if prop.longitude else None,
                },
                'sizeMin': prop.size or '',
                'furnishing': prop.furnishing or 'NO',
                'features': [],  # TODO: Extract from description if needed
                'description': prop.description or '',
                'images': [],  # TODO: Add images if stored
                'scraped_at': prop.created_at.isoformat(),
            })
        
        # Export rentals
        rentals_data = []
        for prop in rent_qs:
            rentals_data.append({
                'id': f"rent_{prop.id}",
                'url': prop.url or '',
                'title': prop.title or '',
                'displayAddress': prop.display_address or '',
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'addedOn': prop.added_on.isoformat() if prop.added_on else None,
                'broker': prop.broker_name or '',
                'agent': prop.agent_name or '',
                'agentPhone': prop.agent_phone or '',
                'verified': prop.verified,
                'reference': prop.reference or '',
                'brokerLicenseNumber': prop.broker_license or '',
                'priceDuration': 'rent',
                'propertyType': prop.property_type or '',
                'price': float(prop.price) if prop.price else 0,
                'priceCurrency': prop.price_currency or 'AED',
                'coordinates': {
                    'latitude': float(prop.latitude) if prop.latitude else None,
                    'longitude': float(prop.longitude) if prop.longitude else None,
                },
                'sizeMin': prop.size or '',
                'furnishing': prop.furnishing or 'NO',
                'features': [],
                'description': prop.description or '',
                'images': [],
                'scraped_at': prop.created_at.isoformat(),
            })
        
        # Combine all data
        all_properties = sales_data + rentals_data
        
        # Save to JSON file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exported_properties_{timestamp}.json"
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_properties, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Exported {len(all_properties)} properties to {filepath}"
                )
            )
            self.stdout.write(f"📊 Sales: {len(sales_data)}, Rentals: {len(rentals_data)}")
            
            # Create latest symlink for easy access
            latest_link = output_dir / "latest_export.json"
            try:
                if latest_link.exists() or latest_link.is_symlink():
                    latest_link.unlink()
                # Create relative symlink for easier portability; on some hosts (e.g., Windows bind mounts)
                # symlink creation may be restricted — handle gracefully.
                latest_link.symlink_to(filepath.name)
                self.stdout.write(f"🔗 Created symlink: {latest_link}")
            except Exception as link_err:
                self.stdout.write(self.style.WARNING(f"⚠️ Could not create symlink: {link_err}"))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Export failed: {e}")
            )
            raise
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pathlib import Path
import json
import logging
from realty.pfimport.models import PFJsonUpload

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import PropertyFinder data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Directory containing JSON files to import'
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
            '--wipe-area',
            action='store_true',
            help='Clear all area data before import'
        )
        parser.add_argument(
            '--wipe-building',
            action='store_true',
            help='Clear all building data before import'
        )

    def handle(self, *args, **options):
        directory = Path(options['directory'])
        
        if not directory.exists():
            raise CommandError(f'Directory {directory} does not exist')
        
        if not directory.is_dir():
            raise CommandError(f'{directory} is not a directory')
        
        # Ищем JSON файлы
        json_files = list(directory.glob('*.json'))
        if not json_files:
            raise CommandError(f'No JSON files found in {directory}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(json_files)} JSON files to process')
        )
        
        # Создаем PFJsonUpload объект
        upload = PFJsonUpload(
            wipe_sale_before=options['wipe_sale'],
            wipe_rent_before=options['wipe_rent'],
            wipe_area_before=options['wipe_area'],
            wipe_buildnig_before=options['wipe_building']
        )
        
        # Обрабатываем каждый файл
        total_processed = 0
        total_errors = 0
        
        for json_file in json_files:
            try:
                self.stdout.write(f'Processing {json_file.name}...')
                
                # Создаем временный файл для Django FileField
                with open(json_file, 'rb') as f:
                    upload.upload_file.save(
                        json_file.name,
                        f,
                        save=False
                    )
                
                # Запускаем импорт
                with transaction.atomic():
                    upload.save()
                
                total_processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed {json_file.name}')
                )
                
            except Exception as e:
                total_errors += 1
                logger.error(f'Error processing {json_file.name}: {e}')
                self.stdout.write(
                    self.style.ERROR(f'Error processing {json_file.name}: {e}')
                )
        
        # Итоговая статистика
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed. Processed: {total_processed}, Errors: {total_errors}'
            )
        )
        
        if total_errors > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'There were {total_errors} errors during import. Check logs for details.'
                )
            )

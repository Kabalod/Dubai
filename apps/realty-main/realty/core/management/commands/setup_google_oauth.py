from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Настройка Google OAuth для django-allauth'

    def handle(self, *args, **options):
        try:
            # Создаем или получаем сайт
            site, site_created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'localhost:8000',
                    'name': 'localhost'
                }
            )
            
            if site_created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Создан новый сайт: {site.domain}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Найден существующий сайт: {site.domain}')
                )
            
            # Получаем реальные Google OAuth credentials из настроек
            client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id-12345')
            client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-secret-12345')
            
            # Создаем или обновляем Google OAuth приложение
            app, app_created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': client_id,
                    'secret': client_secret
                }
            )
            
            # Если приложение уже существует, обновляем credentials
            if not app_created:
                app.client_id = client_id
                app.secret = client_secret
                app.save()
            
            if app_created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Создано новое Google OAuth приложение: {app.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Найдено существующее Google OAuth приложение: {app.name}')
                )
            
            # Добавляем сайт к приложению
            app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Сайт {site.domain} добавлен к приложению {app.name}')
            )
            
            self.stdout.write(f'\n📋 Детали приложения:')
            self.stdout.write(f'   ID: {app.id}')
            self.stdout.write(f'   Provider: {app.provider}')
            self.stdout.write(f'   Name: {app.name}')
            self.stdout.write(f'   Client ID: {app.client_id}')
            self.stdout.write(f'   Sites: {[s.domain for s in app.sites.all()]}')
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Google OAuth настроен успешно!')
            )
            self.stdout.write(
                'Теперь можно тестировать Google вход на http://localhost:8000/accounts/google/login/'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при настройке Google OAuth: {e}')
            )
            import traceback
            traceback.print_exc()

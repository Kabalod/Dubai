"""
Минимальные Django settings ТОЛЬКО для авторизации
Версия: Railway MVP Auth Only
"""
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-auth-only-key-12345')
DEBUG = True
ALLOWED_HOSTS = ['*']

# Минимальные приложения ТОЛЬКО для авторизации
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
]

# Минимальный middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'realty.urls_simple'

# Templates для Django admin
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'realty.wsgi.application'

# Database - восстанавливаем связь с PostgreSQL
import dj_database_url

_db_url = os.environ.get('DATABASE_URL')
if _db_url:
    DATABASES = {
        'default': dj_database_url.parse(_db_url, conn_max_age=600),
    }
else:
    # Fallback к SQLite если PostgreSQL недоступен
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'auth.sqlite3',
        }
    }

# Cache настройки - Redis для Railway, локальный для разработки
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    print(f"🗄️ Настроен Redis кэш: {REDIS_URL}")
else:
    # Fallback к локальному кэшу
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    print(f"🗄️ Настроен локальный кэш (fallback)")

# REST Framework для JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS для frontend
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Google OAuth (простая версия)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'test-client-id')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'test-secret')
# Для совместимости
GOOGLE_OAUTH_CLIENT_ID = GOOGLE_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://workerproject-production.up.railway.app')

# Статические файлы (минимум)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Интернационализация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email настройки - ПРИОРИТЕТ SMTP > SendGrid API > Console/File
# Отключаем SendGrid API в пользу SMTP relay
SENDGRID_API_KEY = None  # os.environ.get('SENDGRID_API_KEY')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mail.kabalod.online')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'

# Отключаем SSL проверку для reg.ru хостинга (из-за несоответствия сертификата)
import ssl
try:
    from django.core.mail.backends.smtp import EmailBackend
    original_open = EmailBackend.open
    
    def patched_open(self):
        if self.connection:
            return False
        try:
            self.connection = self.connection_class(
                self.host, self.port, timeout=self.timeout
            )
            # Отключаем проверку SSL сертификата для reg.ru
            if self.use_tls:
                # Создаем SSL контекст без проверки сертификата
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.connection.starttls(context=context)
            if self.use_ssl:
                # Аналогично для SSL
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
    
    EmailBackend.open = patched_open
    print("📧 SSL проверка отключена для reg.ru хостинга")
except Exception as e:
    print(f"⚠️ Не удалось отключить SSL проверку: {e}")
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'noreply@kabalod.online')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Dubai Real Estate <noreply@kabalod.online>')

# Определяем окружение
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT_NAME') is not None
IS_PRODUCTION = IS_RAILWAY or os.environ.get('NODE_ENV') == 'production'

# Выбираем email backend по приоритету
if EMAIL_HOST_PASSWORD and EMAIL_HOST == 'smtp.sendgrid.net':
    # SendGrid SMTP Relay - высший приоритет (более надежный)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    print(f"📧 НАСТРОЕН SendGrid SMTP Relay: {EMAIL_HOST}:{EMAIL_PORT}")
    print(f"📧 SMTP User: {EMAIL_HOST_USER}")
    
elif SENDGRID_API_KEY:
    # SendGrid API - второй приоритет
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    INSTALLED_APPS.append('anymail')
    
    ANYMAIL = {
        "SENDGRID_API_KEY": SENDGRID_API_KEY,
        "SENDGRID_GENERATE_MESSAGE_ID": True,
        "SENDGRID_MERGE_FIELD_FORMAT": "-{}-",
        "SENDGRID_API_URL": "https://api.sendgrid.com/v3/",
    }
    print(f"📧 НАСТРОЕН SendGrid API для отправки реальных email")
    print(f"📧 SendGrid API Key: {SENDGRID_API_KEY[:20]}...")
    
elif EMAIL_HOST_PASSWORD:
    # SMTP - второй приоритет
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    print(f"📧 НАСТРОЕН SMTP: {EMAIL_HOST}:{EMAIL_PORT}")
    
elif not IS_PRODUCTION:
    # Для разработки - file backend  
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = '/tmp/emails'
    print(f"📧 НАСТРОЕН file backend: {EMAIL_FILE_PATH}")
    
else:
    # Fallback для продакшна
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print(f"📧 НАСТРОЕН console backend (fallback)")

print(f"🌍 Окружение: {'Railway' if IS_RAILWAY else 'Local'}")
print(f"🔧 Email Backend: {EMAIL_BACKEND}")
print(f"📨 From Email: {DEFAULT_FROM_EMAIL}")
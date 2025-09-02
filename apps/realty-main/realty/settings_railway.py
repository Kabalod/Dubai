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

# Добавим anymail если есть SENDGRID_API_KEY
_sendgrid_key = os.environ.get('SENDGRID_API_KEY')
if _sendgrid_key:
    INSTALLED_APPS.append('anymail')

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
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'test-client-id')
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'test-secret')
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

# Email настройки для отправки писем с поддержкой SendGrid
_sendgrid_key = os.environ.get('SENDGRID_API_KEY')

if _sendgrid_key:
    # Используем SendGrid через anymail
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {
        "SENDGRID_API_KEY": _sendgrid_key,
        "SENDGRID_GENERATE_MESSAGE_ID": True,
        "SENDGRID_MERGE_FIELD_FORMAT": "-{}-",
        "SENDGRID_API_URL": "https://api.sendgrid.com/v3/",
    }
    INSTALLED_APPS.append('anymail')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Dubai Real Estate <noreply@kabalod.online>')
else:
    # Fallback к SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mail.kabalod.online')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'noreply@kabalod.online')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Dubai Real Estate <noreply@kabalod.online>')
    
    # Если нет настроек SMTP - используем console backend для development
    if not EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
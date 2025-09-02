import sys
from email.utils import parseaddr
from pathlib import Path

from environs import Env
from marshmallow.validate import Email

# 0. Setup
# --------------------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

APPS_DIR = BASE_DIR / "realty"

env = Env()
env.read_env(Path(BASE_DIR, ".env").as_posix())

# We should strive to only have two possible runtime scenarios: either `DEBUG`
# is True or it is False. `DEBUG` should be only true in development, and
# False when deployed, whether or not it's a production environment.
DEBUG = env.bool("DEBUG", default=False)

PROD = not DEBUG

# 1. Django Core Settings
# -----------------------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/4.0/ref/settings/

# Support both DJANGO_ALLOWED_HOSTS and ALLOWED_HOSTS; include sensible defaults
# Note: Ports in Host header are ignored by Django matching
_dj_allowed_hosts = env.list("DJANGO_ALLOWED_HOSTS", default=None, subcast=str)
if _dj_allowed_hosts is None:
    _dj_allowed_hosts = env.list(
        "ALLOWED_HOSTS",
        default=["*"] if DEBUG else ["localhost", "127.0.0.1", "backend-production-dbb4.up.railway.app"],
        subcast=str,
    )
ALLOWED_HOSTS = _dj_allowed_hosts

ASGI_APPLICATION = "realty.asgi.application"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
# Включать diskcache только если явно указано переменной окружения
if PROD and env.bool("USE_DISKCACHE", default=False):
    # https://grantjenks.com/docs/diskcache/tutorial.html#djangocache
    CACHES["default"] = {
        "BACKEND": "diskcache.DjangoCache",
        "LOCATION": env.str("CACHE_LOCATION", default=".diskcache"),
        "TIMEOUT": 300,
        "SHARDS": 8,
        "DATABASE_TIMEOUT": 0.010,  # 10 milliseconds
        "OPTIONS": {"size_limit": 2**30},  # 1 gigabyte
    }

CSRF_COOKIE_SECURE = PROD

DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default="sqlite:///db.sqlite3"),
    "tasks_db": env.dj_db_url(
        "TASKS_DATABASE_URL", default="sqlite:///tasks_db.sqlite3"
    ),
}
DATABASES["tasks_db"]["OPTIONS"] = {"transaction_mode": "EXCLUSIVE"}
if PROD:
    if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
        # https://blog.pecar.me/sqlite-django-config
        # https://blog.pecar.me/sqlite-prod
        DATABASES["default"]["OPTIONS"] = {
            "transaction_mode": "IMMEDIATE",
            "init_command": """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA mmap_size = 134217728;
                PRAGMA journal_size_limit = 27103364;
                PRAGMA cache_size=2000;
            """,
        }
    elif DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
        DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Полностью отключено роутирование через falco для MVP
DATABASE_ROUTERS = []

# Django Tasks настройки
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
        "QUEUES": {
            "default": {
                "timeout": 300,
            }
        }
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FROM_EMAIL = env.str(
    "DEFAULT_FROM_EMAIL",
    default="tobidegnon@proton.me",
    validate=lambda v: Email()(parseaddr(v)[1]),
)

# Email backend can be overridden via env. Default:
# Email backend: приоритет SendGrid через Anymail → SMTP → console
_smtp_host = env.str("EMAIL_HOST", default=None)
_smtp_user = env.str("EMAIL_HOST_USER", default=None)
_smtp_pass = env.str("EMAIL_HOST_PASSWORD", default=None)
_sendgrid_key = env.str("SENDGRID_API_KEY", default=None)

if _sendgrid_key:
    INSTALLED_APPS = [*DJANGO_APPS, *THIRD_PARTY_APPS, "anymail", *LOCAL_APPS]
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
else:
    EMAIL_BACKEND = env.str(
        "EMAIL_BACKEND",
        default=(
            "django.core.mail.backends.smtp.EmailBackend" if all([_smtp_host, _smtp_user, _smtp_pass]) else "django.core.mail.backends.console.EmailBackend"
        ),
    )

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    # Django REST Framework for MVP API
    "rest_framework",
    # Django Tasks для асинхронных задач
    "django_tasks",
    "django_tasks.backends.database", # <-- Добавлено для поддержки DatabaseBackend
    # Temporarily disabled for Railway MVP
    # "rest_framework_simplejwt",
    # "rest_framework_simplejwt.token_blacklist",
    # "anymail",
]

LOCAL_APPS = [
    # Все необходимые приложения
    "realty.api",      # MVP REST API
    "realty.main",     # Основные модели (Building, MasterProject)
    "realty.pfimport", # Property Finder модели (Area, Building, PFListSale, PFListRent)
    "realty.building_reports", # Отчеты по зданиям
    "realty.reports",  # Система отчетов
]

if DEBUG:
    # Development only apps
    THIRD_PARTY_APPS = [
        "debug_toolbar",
        "whitenoise.runserver_nostatic",
        "django_browser_reload",
        # "django_fastdev",
        # "django_watchfiles", # currently not working when html files are changed
        *THIRD_PARTY_APPS,
    ]

INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + DJANGO_APPS

if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "10.0.2.2",
    ]

LANGUAGE_CODE = "en-us"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain_console": {
            "format": "%(levelname)s %(message)s",
        },
        "verbose": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["stdout"],
            "level": env.log_level("DJANGO_LOG_LEVEL", default="INFO"),
        },
        "realty": {
            "handlers": ["stdout"],
            "level": env.log_level("REALTY_LOG_LEVEL", default="INFO"),
        },
    },
}

MEDIA_ROOT = env.path("MEDIA_ROOT", default=APPS_DIR / "media")

MEDIA_URL = "/media/"

# https://docs.djangoproject.com/en/dev/topics/http/middleware/
# https://docs.djangoproject.com/en/dev/ref/middleware/#middleware-ordering
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # order doesn't matter
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Отключено для MVP (убрали allauth urls)
    # "allauth.account.middleware.AccountMiddleware",
    # Метрики HTTP для API
    "realty.api.middleware.MetricsMiddleware",
]
if DEBUG:
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    )

ROOT_URLCONF = "realty.urls"

SECRET_KEY = env.str(
    "SECRET_KEY", default="django-insecure-KOjdmOK1ICbbtgFagYmV5iBUp0Y2J37FES98BU9As24"
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = PROD

SECURE_HSTS_PRELOAD = PROD

# https://docs.djangoproject.com/en/dev/ref/middleware/#http-strict-transport-security
# 2 minutes to start with, will increase as HSTS is tested
# example of production value: 60 * 60 * 24 * 7 = 604800 (1 week)
SECURE_HSTS_SECONDS = 0 if DEBUG else env.int("SECURE_HSTS_SECONDS", default=60 * 2)

# https://noumenal.es/notes/til/django/csrf-trusted-origins/
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SECURE_SSL_REDIRECT можно принудительно включать в продакшне или через ENV
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)

SERVER_EMAIL = env.str(
    "SERVER_EMAIL",
    default=DEFAULT_FROM_EMAIL,
    validate=lambda v: Email()(parseaddr(v)[1]),
)

SESSION_COOKIE_SECURE = PROD

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
if PROD and env.bool("USE_S3", default=False):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": env.str("AWS_ACCESS_KEY_ID", default=None),
            "bucket_name": env.str("AWS_STORAGE_BUCKET_NAME", default=None),
            "region_name": env.str("AWS_S3_REGION_NAME", default=None),
            "secret_key": env.str("AWS_SECRET_ACCESS_KEY", default=None),
        },
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

TIME_ZONE = "UTC"

USE_I18N = False

USE_TZ = True

WSGI_APPLICATION = "realty.wsgi.application"

# 2. Django Contrib Settings
# -----------------------------------------------------------------------------------------------

# django.contrib.auth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []

# django.contrib.staticfiles
STATIC_ROOT = APPS_DIR / "staticfiles"

STATIC_URL = "/static/"

# Добавляем каталог со статикой только если он существует, чтобы избежать предупреждений
_project_static_dir = APPS_DIR / "static"
STATICFILES_DIRS = [_project_static_dir] if _project_static_dir.exists() else []

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# 3. Third Party Settings
# -------------------------------------------------------------------------------------------------

# django-allauth
# ACCOUNT_LOGIN_METHODS = {"email"}
# ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
# Frontend URL for OAuth redirects (берём из ENV; без хардкодов старых доменов)
FRONTEND_URL = env.str("FRONTEND_URL", default=None) or ""

# Google OAuth settings - теперь из переменных окружения
GOOGLE_OAUTH_CLIENT_ID = env.str("GOOGLE_CLIENT_ID", default="test-client-id-12345")
GOOGLE_OAUTH_CLIENT_SECRET = env.str("GOOGLE_CLIENT_SECRET", default="test-secret-12345")
GOOGLE_OAUTH_REDIRECT_URI = env.str("GOOGLE_OAUTH_REDIRECT_URI", default="https://dubai.up.railway.app/api/auth/google/callback/")

# ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
# ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"
# ACCOUNT_SESSION_REMEMBER = True
# ACCOUNT_UNIQUE_EMAIL = True
# LOGIN_REDIRECT_URL = "home"
# SOCIALACCOUNT_PROVIDERS = {
#     "google": {
#         "AUTH_PARAMS": {"access_type": "online"},
#         "EMAIL_AUTHENTICATION": True,
#         "OAUTH_PKCE_ENABLED": True,
#         "SCOPE": ["profile", "email"],
#     }
# }

# Email configuration simplified for Railway deployment
# SendGrid integration removed for MVP

# SMTP (например, Яндекс/Почта.ру). Активируется, если EMAIL_BACKEND =
# "django.core.mail.backends.smtp.EmailBackend"
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = _smtp_host or env.str("EMAIL_HOST", default="smtp.yandex.ru")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = _smtp_user or env.str("EMAIL_HOST_USER", default=None)
    EMAIL_HOST_PASSWORD = _smtp_pass or env.str("EMAIL_HOST_PASSWORD", default=None)
    # По умолчанию 587/TLS, можно переключить на 465/SSL через переменные
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)

# django-debug-toolbar
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
    "SHOW_COLLAPSED": True,
    "UPDATE_ON_FETCH": True,
    "ROOT_TAG_EXTRA_ATTRS": "hx-preserve",
}

# django-corsheaders
# Prefer explicit origins via env; otherwise используем FRONTEND_URL и локальные адреса
_cors_env = env.list("CORS_ALLOWED_ORIGINS", default=None)
if _cors_env is not None:
    CORS_ALLOWED_ORIGINS = _cors_env
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
    ]
    if FRONTEND_URL:
        CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

# Allow all only during development
CORS_ALLOW_ALL_ORIGINS = DEBUG

# CSRF trusted origins — из ENV или из FRONTEND_URL
_csrf_env = env.list("CSRF_TRUSTED_ORIGINS", default=None)
if _csrf_env is not None:
    CSRF_TRUSTED_ORIGINS = _csrf_env
else:
    CSRF_TRUSTED_ORIGINS = []
    if FRONTEND_URL:
        CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)

# django-litestream
LITESTREAM = {
    "config_file": BASE_DIR / "litestream.yml",
}

# django-tasks
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
        "OPTIONS": {"database": "tasks_db"},
    }
}

# Sentry отключен для минимальной конфигурации


CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"

CRISPY_TEMPLATE_PACK = "tailwind"

# 4. Project Settings
# -----------------------------------------------------------------------------------------------------

ADMIN_URL = env.str("ADMIN_URL", default="admin/")


# ========================================
# Django REST Framework Settings for MVP
# ========================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Settings for Frontend
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# django-anymail
if PROD:
    ANYMAIL = {
        "SENDGRID_API_KEY": env.str("SENDGRID_API_KEY", default=None),
        "SENDGRID_GENERATE_MESSAGE_ID": True,
        "SENDGRID_MERGE_FIELD_FORMAT": "-{}-",
        "SENDGRID_API_URL": "https://api.sendgrid.com/v3/",
    }

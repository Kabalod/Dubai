# Backend Audit (Dubai MVP)

## Обзор

- Стек: Django 4.2/5.1 (разнородные конфиги), Python 3.12, DRF, SimpleJWT, Whitenoise
- Развёртывание: Railway (Dockerfile.railway), compose для локалки/прода
- Цель: MVP API + OTP-аутентификация, mock-данные недвижимости

## Найденные проблемы

- Дубли кода `realty/*` в корне и `apps/realty-main/realty/*` → риск конфликтов импортов и миграций
- Кастомная модель `User` в `realty/api/models.py` и миграции `0004_*` не активирована через `AUTH_USER_MODEL` → конфликт с стандартной `auth.User`
- Несогласованность настроек: `settings.py` и `settings_railway.py` расходятся по приложениям (JWT, anymail), CORS и базе
- Stripe webhook: отсутствие безопасной обработки при пустом `STRIPE_WEBHOOK_SECRET`
- Prod-команда в compose использует `runserver` вместо Gunicorn, нет `collectstatic`/`migrate`
- Экспорт Prometheus метрик отсутствует (middleware есть)

## Внесённые правки (в этой итерации)

- Docker: обновлён `Dockerfile.railway` (Python 3.12, копирование из `apps/realty-main`, healthcheck `/api/health/`, `DJANGO_SETTINGS_MODULE=realty.settings_railway`)
- Зависимости: добавлены `environs[django]`, `psycopg[binary]`, `whitenoise[brotli]`, `djangorestframework-simplejwt`, `prometheus-client`
- Настройки Railway: включён JWT, Whitenoise, `MetricsMiddleware`, добавлены `ADMIN_URL`, `FRONTEND_URL`, `STRIPE_WEBHOOK_SECRET`
- ASGI: переключён на `settings_railway`
- Сериализаторы: переведены на `get_user_model()`
- Views: удалён дубликат `PropertyDetailView`

## Рекомендации (следующие шаги)

1. Удалить кастомный `User` и миграции, связанные с ним, из `realty/api` (или официально ввести `AUTH_USER_MODEL` и пересобрать миграции)
2. Удалить/исключить корневую копию `realty/*`, оставить единственный путь `apps/realty-main/realty/*`
3. Ввести entrypoint: `migrate && collectstatic && gunicorn realty.wsgi:application` для prod и обновить compose
4. Добавить `/metrics` endpoint (или интегрировать `django-prometheus`) и целевой скрейп в Prometheus
5. В `settings_railway.py` переключить БД на `DATABASE_URL` при наличии переменной окружения
6. Свести `settings.py`/`settings_railway.py` к единой базе, различия выносить в ENV

## Контрольный список

- [ ] Удалён кастомный User и миграции
- [ ] Устранены дубли `realty/*`
- [ ] Обновлён prod запуск (gunicorn + миграции + статика)
- [ ] Добавлен `/metrics`
- [ ] Проверен переход на Postgres через `DATABASE_URL`

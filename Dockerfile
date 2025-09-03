# 🔥 Railway Django Backend Dockerfile - ТОЛЬКО для авторизации
# Минимальный Django Dockerfile для Railway deployment
# EMERGENCY FIX - КРИТИЧНОЕ ИСПРАВЛЕНИЕ auth_views_simple
FROM python:3.11-slim

# Принудительная очистка кеша - EMERGENCY REBUILD v8
ARG CACHE_BUST=2025-01-30-08-00-EMERGENCY-REBUILD-v8
ENV CACHE_BUST=${CACHE_BUST}

# Метки для идентификации - ДОЛЖНЫ БЫТЬ ВИДНЫ RAILWAY
LABEL cache-bust="2025-01-30-08-00-EMERGENCY-REBUILD-v8"
LABEL service="django-backend"
LABEL auth-only="true"
LABEL railway-deployment="true"
LABEL auth-views-simple="EMERGENCY-FIXED"
LABEL build-timestamp="2025-01-30-16-00"
LABEL commit-hash="3c97fa6"

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements.txt сначала
COPY apps/realty-main/requirements.txt .

# Минимальные Python зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем ТОЛЬКО необходимые файлы для авторизации из apps/realty-main/
# ВАЖНО: Используем auth_views_simple.py, а НЕ auth_views.py!
# RAILWAY: Обязательно скопировать ТОЛЬКО auth_views_simple.py!
COPY apps/realty-main/manage.py .
COPY apps/realty-main/realty/__init__.py ./realty/
COPY apps/realty-main/realty/settings_railway.py ./realty/
COPY apps/realty-main/realty/urls_simple.py ./realty/
COPY apps/realty-main/realty/auth_views_simple.py ./realty/  # RAILWAY: ЭТОТ ФАЙЛ ОБЯЗАТЕЛЬНО!
COPY apps/realty-main/realty/wsgi.py ./realty/

# ПРОВЕРКА: Убедимся что правильный файл скопирован (для Railway)
RUN ls -la ./realty/ | grep auth_views && \
    echo "RAILWAY: Проверяем наличие auth_views_simple.py..." && \
    if [ -f "./realty/auth_views_simple.py" ]; then \
        echo "✅ RAILWAY: auth_views_simple.py найден!"; \
    else \
        echo "❌ RAILWAY: auth_views_simple.py НЕ найден!"; \
        exit 1; \
    fi

# Environment variables
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=realty.settings_railway
ENV PYTHONUNBUFFERED=1

# Создаем базу данных
RUN python manage.py migrate

# Создаем админа (опционально)
RUN echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@test.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Порт
EXPOSE 8000

# Запуск с Railway PORT переменной
CMD ["sh", "-c", "gunicorn realty.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile - --error-logfile - --log-level debug"]
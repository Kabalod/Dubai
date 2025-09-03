# 🔥 Railway Django Backend Dockerfile - ТОЛЬКО для авторизации
# Минимальный Django Dockerfile для Railway deployment
FROM python:3.11-slim

# Принудительная очистка кеша - FORCE REBUILD v3
ARG CACHE_BUST=2025-01-30-03-00-FORCE-REBUILD-v3
ENV CACHE_BUST=${CACHE_BUST}

# Метки для идентификации
LABEL cache-bust="2025-01-30-03-00-FORCE-REBUILD-v3"
LABEL service="django-backend"
LABEL auth-only="true"
LABEL railway-deployment="true"

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Минимальные Python зависимости
COPY apps/realty-main/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Создаем директорию realty перед копированием
RUN mkdir -p ./realty

# Копируем ТОЛЬКО необходимые файлы для авторизации из apps/realty-main/
# ВАЖНО: Используем auth_views_simple.py, а НЕ auth_views.py!
COPY apps/realty-main/manage.py .
COPY apps/realty-main/realty/__init__.py ./realty/
COPY apps/realty-main/realty/settings_railway.py ./realty/
COPY apps/realty-main/realty/urls_simple.py ./realty/
COPY apps/realty-main/realty/auth_views_simple.py ./realty/  # ← КОРРЕКТНЫЙ ФАЙЛ
COPY apps/realty-main/realty/wsgi.py ./realty/

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
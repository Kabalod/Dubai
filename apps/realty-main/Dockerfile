# Minimal Django Dockerfile - ТОЛЬКО для авторизации
FROM python:3.11-slim

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Мистнимальные Python зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем ТОЛЬКО необходимые файлы для авторизации
COPY manage.py .
COPY realty/__init__.py ./realty/
COPY realty/settings_railway.py ./realty/
COPY realty/urls_simple.py ./realty/
COPY realty/auth_views.py ./realty/
COPY realty/wsgi.py ./realty/

# Добавляем cache bust для принудительного обновления
ENV CACHE_BUST=2025-01-30-01-30

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

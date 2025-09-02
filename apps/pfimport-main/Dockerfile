# MVP Dockerfile для парсера PropertyFinder
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание shared-data директории и установка прав
RUN mkdir -p /shared-data \
    && mkdir -p /app/logs \
    && chmod 755 /shared-data \
    && chmod 755 /app/logs

# Создание пользователя (безопасность)
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app \
    && chown -R app:app /shared-data

# Создание Django superuser script (опционально)
RUN echo '#!/bin/bash\npython manage.py migrate\nexec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && chown app:app /app/entrypoint.sh

USER app

# Health check (унификация с compose: ожидаем /health/)
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Запуск приложения
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
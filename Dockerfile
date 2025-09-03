# 🔥 BRAND NEW Railway Django Dockerfile - FINAL SOLUTION
# Полностью новый файл для Railway deployment
# CRITICAL: auth_views_simple.py MUST BE USED
FROM python:3.11-slim

# FORCE REBUILD v11 - BRAND NEW
ARG CACHE_BUST=2025-01-30-11-00-BRAND-NEW-v11
ENV CACHE_BUST=${CACHE_BUST}

# CRITICAL LABELS FOR RAILWAY
LABEL cache-bust="2025-01-30-11-00-BRAND-NEW-v11"
LABEL service="django-backend"
LABEL auth-only="true"
LABEL railway-deployment="true"
LABEL auth-views-simple="REQUIRED"
LABEL build-timestamp="2025-01-30-17-00"
LABEL commit-hash="303a416"
LABEL emergency-rebuild="true"
LABEL webhook-trigger="force"
LABEL dockerfile-version="brand-new-v11"

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY apps/realty-main/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# CRITICAL: Copy Django files - auth_views_simple.py MUST BE INCLUDED
COPY apps/realty-main/manage.py .
RUN mkdir -p ./realty

# Copy each file individually to ensure auth_views_simple.py is included
COPY apps/realty-main/realty/__init__.py ./realty/
COPY apps/realty-main/realty/settings_railway.py ./realty/
COPY apps/realty-main/realty/urls_simple.py ./realty/
COPY apps/realty-main/realty/auth_views_simple.py ./realty/
COPY apps/realty-main/realty/wsgi.py ./realty/

# VERIFY: Check that the correct file was copied
RUN echo "=== RAILWAY VERIFICATION ===" && \
    ls -la ./realty/ && \
    echo "Checking for auth_views_simple.py..." && \
    if [ -f "./realty/auth_views_simple.py" ]; then \
        echo "✅ SUCCESS: auth_views_simple.py found!"; \
        ls -la ./realty/auth_views_simple.py; \
    else \
        echo "❌ FAILED: auth_views_simple.py NOT found!"; \
        ls -la ./realty/; \
        exit 1; \
    fi

# Environment variables
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=realty.settings_railway
ENV PYTHONUNBUFFERED=1

# Run migrations
RUN echo "=== STARTING MIGRATIONS ===" && \
    python manage.py migrate

# Create superuser
RUN echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@test.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Final verification
RUN echo "=== FINAL VERIFICATION ===" && \
    ls -la ./realty/auth_views_simple.py && \
    echo "✅ BUILD SUCCESSFUL: auth_views_simple.py is present"

EXPOSE 8000

# Start Gunicorn
CMD ["sh", "-c", "gunicorn realty.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile - --error-logfile - --log-level debug"]

# 🐳 Docker Guide - Dubai MVP

Полное руководство по использованию Docker в проекте Dubai MVP.

## 📋 Содержание

- [🏗️ Архитектура](#️-архитектура)
- [🚀 Быстрый старт](#-быстрый-старт)
- [🔧 Конфигурация](#-конфигурация)
- [📊 Мониторинг](#-мониторинг)
- [🔍 Troubleshooting](#-troubleshooting)
- [🛡️ Безопасность](#️-безопасность)

## 🏗️ Архитектура

### Сервисы

```
Dubai MVP Docker Stack
├── 🗄️ postgres (Database)
├── 🔴 redis (Cache)
├── 🐍 backend (Django API)
├── ⚛️ frontend (React SPA)
├── 🌐 nginx (Reverse Proxy)
├── 📊 prometheus (Metrics)
└── 📈 grafana (Dashboards)
```

### Сети и Volumes

```yaml
Networks:
  - dubai_network (172.20.0.0/16)

Volumes:
  - postgres_data (Database)
  - redis_data (Cache)
  - media_files (User uploads)
  - static_files (Static assets)
  - prometheus_data (Metrics)
  - grafana_data (Dashboards)
```

## 🚀 Быстрый старт

### 1. Подготовка

```bash
# Клонирование репозитория
git clone https://github.com/Kabalod/Workerproject.git
cd Workerproject

# Копирование переменных окружения
cp env.example .env
# Отредактируйте .env файл своими значениями
```

### 2. Разработка

```bash
# Запуск для разработки
docker-compose -f docker-compose.dev.yml up --build

# Или через автоматизированный менеджер
.\manage-project.ps1 dev
```

**Доступные сервисы:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin/
- Database: localhost:5432

### 3. Продакшен

```bash
# Запуск production stack
docker-compose -f docker-compose.production.yml up -d

# С мониторингом
docker-compose -f docker-compose.production.yml --profile monitoring up -d
```

**Доступные сервисы:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Nginx: http://localhost (reverse proxy)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## 🔧 Конфигурация

### Backend Dockerfile

```dockerfile
# Оптимизированный многослойный образ
FROM python:3.11-slim AS base

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Безопасность: непривилегированный пользователь
RUN groupadd -r django && useradd -r -g django django

# Python зависимости (кешируемый слой)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . /app
WORKDIR /app
RUN chown -R django:django /app
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### Frontend Dockerfile

```dockerfile
# Multi-stage build для оптимизации размера
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json yarn.lock ./
RUN corepack enable && yarn install --frozen-lockfile
COPY . .
RUN yarn build

# Production образ с Nginx
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

### Переменные окружения

Создайте `.env` файл из `env.example`:

```bash
# Database
POSTGRES_PASSWORD=secure_password_change_me
REDIS_PASSWORD=secure_redis_password

# Django
SECRET_KEY=your-secret-key-here
DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Email
SENDGRID_API_KEY=your-sendgrid-key
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

## 📊 Мониторинг

### Включение мониторинга

```bash
# Запуск с Prometheus и Grafana
docker-compose -f docker-compose.production.yml --profile monitoring up -d
```

### Доступные метрики

- **Prometheus**: http://localhost:9090
  - Django метрики
  - PostgreSQL метрики
  - Redis метрики
  - Nginx метрики

- **Grafana**: http://localhost:3001 (admin/admin)
  - Дашборды системы
  - Алерты
  - Логи

### Health Checks

Все сервисы имеют встроенные health checks:

```bash
# Проверка статуса всех сервисов
docker-compose ps

# Логи конкретного сервиса
docker-compose logs backend

# Мониторинг в реальном времени
docker-compose logs -f backend
```

## 🔍 Troubleshooting

### Частые проблемы

#### 1. Backend не запускается

```bash
# Проверка логов
docker-compose logs backend

# Проверка переменных окружения
docker-compose exec backend env | grep DJANGO

# Проверка подключения к БД
docker-compose exec backend python manage.py dbshell
```

#### 2. Frontend не собирается

```bash
# Проверка логов сборки
docker-compose logs frontend

# Пересборка без кеша
docker-compose build --no-cache frontend

# Проверка зависимостей
docker-compose exec frontend yarn list
```

#### 3. Database проблемы

```bash
# Проверка статуса PostgreSQL
docker-compose exec postgres pg_isready

# Подключение к БД
docker-compose exec postgres psql -U postgres -d dubai_mvp

# Восстановление из бэкапа
docker-compose exec postgres psql -U postgres -d dubai_mvp < backup.sql
```

#### 4. Проблемы с портами

```bash
# Проверка занятых портов
netstat -tulpn | grep :8000

# Остановка всех контейнеров
docker-compose down

# Очистка системы
docker system prune -f
```

### Диагностические команды

```bash
# Статус всех сервисов
docker-compose ps

# Использование ресурсов
docker stats

# Логи всех сервисов
docker-compose logs

# Подключение к контейнеру
docker-compose exec backend bash

# Проверка сети
docker network ls
docker network inspect dubai_mvp_dubai_network
```

## 🛡️ Безопасность

### Лучшие практики

#### 1. Непривилегированные пользователи

```dockerfile
# Создание пользователя
RUN groupadd -r django && useradd -r -g django django
USER django
```

#### 2. Минимальные образы

```dockerfile
# Используйте alpine или slim образы
FROM python:3.11-slim
FROM node:20-alpine
FROM nginx:1.25-alpine
```

#### 3. Секреты

```bash
# Никогда не храните секреты в Dockerfile
# Используйте переменные окружения или Docker secrets

# Для production используйте Docker secrets
echo "my_secret" | docker secret create db_password -
```

#### 4. Сетевая безопасность

```yaml
# Изолированные сети
networks:
  dubai_network:
    driver: bridge
    internal: true  # Только для внутренних сервисов
```

#### 5. Обновления безопасности

```bash
# Регулярно обновляйте базовые образы
docker pull python:3.11-slim
docker pull node:20-alpine
docker pull nginx:1.25-alpine

# Пересборка с обновлениями
docker-compose build --no-cache
```

### Сканирование уязвимостей

```bash
# Установка Docker Scout
docker scout quickview

# Сканирование образа
docker scout cves local://dubai_backend:latest

# Рекомендации по исправлению
docker scout recommendations local://dubai_backend:latest
```

## 📝 Полезные команды

### Управление контейнерами

```bash
# Запуск в фоне
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск сервиса
docker-compose restart backend

# Масштабирование
docker-compose up -d --scale backend=3
```

### Очистка

```bash
# Удаление неиспользуемых образов
docker image prune -f

# Удаление всех остановленных контейнеров
docker container prune -f

# Полная очистка системы
docker system prune -a -f --volumes
```

### Бэкапы

```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres dubai_mvp > backup.sql

# Бэкап volumes
docker run --rm -v dubai_mvp_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Восстановление
docker run --rm -v dubai_mvp_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

---

## 🎯 Заключение

Docker конфигурация Dubai MVP оптимизирована для:
- ⚡ **Быстрой разработки** с hot reload
- 🚀 **Production deployment** с безопасностью
- 📊 **Мониторингом** и логированием
- 🔧 **Легкой отладкой** и troubleshooting

Для получения помощи обращайтесь к [Issues](https://github.com/Kabalod/Workerproject/issues) или пишите на kbalodk@gmail.com.

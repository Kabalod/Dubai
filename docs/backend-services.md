# Backend сервисы

## Обзор

Архитектура и описание backend сервисов проекта Dubai.

## Основные сервисы

### Real Estate API
- **Порт (host:container)**: 8090:8000 (prod compose)
- **Технология**: Django + DRF + GraphQL
- **Описание**: Основной API для работы с недвижимостью
- **Health**: `GET /api/health/` → 200 JSON (proxy в Nginx: `/health/api`)
- **ENV**:
  - `DJANGO_ALLOWED_HOSTS`: должен включать `localhost`, `127.0.0.1`, и прод-домен
  - `CORS_ALLOWED_ORIGINS`: `http://localhost:3000`, `http://localhost`, и прод-домен
  - `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`
  - `SECURE_SSL_REDIRECT` (по умолчанию = `PROD`, можно переопределить)
  
Пример prod compose (фрагмент):
```yaml
api-service:
  ports:
    - "${API_PORT:-8090}:8000"
  environment:
    - DJANGO_ALLOWED_HOSTS=${API_ALLOWED_HOSTS:-api-service,localhost,127.0.0.1,yourdomain.com}
    - CORS_ALLOWED_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://localhost,https://yourdomain.com}
```

### Analytics Service
- **Порт**: 8001
- **Технология**: FastAPI + Pandas
- **Описание**: Сервис аналитики и отчетов

### Data Processing
- **Порт**: 8002
- **Технология**: Celery + Redis
- **Описание**: ETL процессы и обработка данных

## Архитектура

### Микросервисная архитектура
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Real Estate   │    │   Analytics     │    │ Data Processing │
│     API        │    │    Service      │    │    Service      │
│   (Django)     │    │   (FastAPI)     │    │   (Celery)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   + pgvector    │
                    └─────────────────┘
```

### Взаимодействие сервисов
- **API Gateway**: Nginx как reverse proxy
- **База данных**: PostgreSQL с расширением pgvector
- **Кэш**: Redis для сессий и временных данных
- **Очереди**: Celery для асинхронных задач

## API Endpoints

### Real Estate API
```python
## Основные endpoints
GET    /api/real-estate/          # Список объектов
GET    /api/real-estate/{id}/     # Детали объекта
POST   /api/real-estate/          # Создание объекта
PUT    /api/real-estate/{id}/     # Обновление объекта
DELETE /api/real-estate/{id}/     # Удаление объекта

## GraphQL endpoint
POST   /graphql/                  # GraphQL API

## Health
GET    /api/health/               # 200 JSON (health/status)
```

### Analytics Service
```python
## Аналитические endpoints
GET    /api/analytics/market/     # Рыночные данные
GET    /api/analytics/trends/     # Тренды рынка
GET    /api/analytics/reports/    # Готовые отчеты
POST   /api/analytics/query/      # Кастомные запросы
```

### Data Processing
```python
## ETL endpoints
POST   /api/etl/import/          # Импорт данных
GET    /api/etl/status/{task_id}/ # Статус задачи
GET    /api/etl/history/         # История импортов
```

## База данных

### Схема данных
```sql
-- Основные таблицы
CREATE TABLE real_estate (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    price DECIMAL(10,2),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    date DATE,
    area VARCHAR(100),
    avg_price DECIMAL(10,2),
    volume INTEGER
);

CREATE TABLE ai_memory (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Индексы и оптимизация
- **pgvector**: Для семантического поиска
- **B-tree**: Для стандартных запросов
- **GIN**: Для полнотекстового поиска

## Мониторинг

### Метрики
- Response time
- Throughput
- Error rate
- Database performance

### Логирование
- Structured logging (JSON)
- Centralized log collection
- Log rotation и архивирование

## Развертывание

### Docker Compose
```yaml
version: '3.8'
services:
  real-estate-api:
    image: dubai/real-estate-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dubai
      - REDIS_URL=redis://redis:6379

  analytics-service:
    image: dubai/analytics-service
    ports:
      - "8001:8001"
    depends_on:
      - db
      - redis

  data-processor:
    image: dubai/data-processor
    ports:
      - "8002:8002"
    depends_on:
      - db
      - redis
```

## Связанные документы

- [Обзор системы](./OVERVIEW.md)
- [Frontend API](./frontend-api.md)
- [AI агенты](./ai-agents.md)
- [База данных](./database-schema.md)
- [Аутентификация](./authentication.md)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025


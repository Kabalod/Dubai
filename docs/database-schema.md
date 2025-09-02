# Схема базы данных

## Обзор

Подробное описание структуры базы данных проекта Dubai.

## Основные таблицы

### Real Estate (Недвижимость)
```sql
CREATE TABLE real_estate (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(12,2),
    price_currency VARCHAR(3) DEFAULT 'AED',
    property_type VARCHAR(50),
    bedrooms INTEGER,
    bathrooms INTEGER,
    area_sqft DECIMAL(10,2),
    location VARCHAR(255),
    district VARCHAR(100),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'UAE',
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Market Data (Рыночные данные)
```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    area VARCHAR(100),
    district VARCHAR(100),
    property_type VARCHAR(50),
    avg_price DECIMAL(12,2),
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    volume INTEGER,
    days_on_market INTEGER,
    price_per_sqft DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### AI Memory (Память AI)
```sql
CREATE TABLE ai_memory (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50),
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW()
);
```

### Users (Пользователи)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Transactions (Транзакции)
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES real_estate(id),
    transaction_type VARCHAR(20), -- 'sale', 'rent'
    price DECIMAL(12,2),
    transaction_date DATE,
    buyer_id INTEGER REFERENCES users(id),
    seller_id INTEGER REFERENCES users(id),
    agent_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Индексы

### Основные индексы
```sql
-- Индексы для быстрого поиска
CREATE INDEX idx_real_estate_location ON real_estate(location);
CREATE INDEX idx_real_estate_price ON real_estate(price);
CREATE INDEX idx_real_estate_property_type ON real_estate(property_type);
CREATE INDEX idx_real_estate_status ON real_estate(status);

-- Геопространственные индексы
CREATE INDEX idx_real_estate_coords ON real_estate USING GIST (
    ll_to_earth(latitude, longitude)
);

-- Векторные индексы для AI
CREATE INDEX idx_ai_memory_embedding ON ai_memory USING ivfflat (embedding vector_cosine_ops);

-- Составные индексы
CREATE INDEX idx_market_data_area_date ON market_data(area, date);
CREATE INDEX idx_transactions_property_date ON transactions(property_id, transaction_date);
```

### Полнотекстовый поиск
```sql
-- Индекс для полнотекстового поиска
ALTER TABLE real_estate ADD COLUMN search_vector tsvector;
CREATE INDEX idx_real_estate_search ON real_estate USING GIN(search_vector);

-- Триггер для обновления search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.location, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_real_estate_search_vector
    BEFORE INSERT OR UPDATE ON real_estate
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

## Связи между таблицами

### ER диаграмма
```
real_estate (1) ←→ (N) transactions
     ↑                    ↑
     │                    │
     │                    │
users (1) ←→ (N) transactions
     ↑
     │
     │
ai_memory (N) ←→ (1) users
```

### Foreign Keys
```sql
-- Связи для transactions
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_property 
FOREIGN KEY (property_id) REFERENCES real_estate(id);

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_buyer 
FOREIGN KEY (buyer_id) REFERENCES users(id);

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_seller 
FOREIGN KEY (seller_id) REFERENCES users(id);

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_agent 
FOREIGN KEY (agent_id) REFERENCES users(id);
```

## Расширения PostgreSQL

### pgvector для AI
```sql
-- Установка расширения
CREATE EXTENSION IF NOT EXISTS vector;

-- Функция для поиска похожих документов
CREATE OR REPLACE FUNCTION find_similar_memory(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    id int,
    content text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ai_memory.id,
        ai_memory.content,
        1 - (ai_memory.embedding <=> query_embedding) AS similarity
    FROM ai_memory
    WHERE 1 - (ai_memory.embedding <=> query_embedding) > match_threshold
    ORDER BY ai_memory.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

## Миграции

### Пример миграции
```python
## Django migration example
from django.db import migrations, models
import django.contrib.postgres.fields

class Migration(migrations.Migration):
    dependencies = [
        ('real_estate', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='realestate',
            name='amenities',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name='realestate',
            name='floor_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
```

## Мониторинг и оптимизация

### Статистика таблиц
```sql
-- Анализ размера таблиц
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename IN ('real_estate', 'market_data', 'ai_memory')
ORDER BY tablename, attname;

-- Анализ индексов
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('real_estate', 'market_data', 'ai_memory');
```

### Автоочистка
```sql
-- Настройка автоочистки
ALTER TABLE real_estate SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE market_data SET (autovacuum_vacuum_scale_factor = 0.05);
ALTER TABLE ai_memory SET (autovacuum_vacuum_scale_factor = 0.2);
```

## Связанные документы

- [Обзор системы](./OVERVIEW.md)
- [Backend сервисы](./backend-services.md)
- [Frontend API](./frontend-api.md)
- [AI агенты](./ai-agents.md)
- [Аутентификация](./authentication.md)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025


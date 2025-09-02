# 📚 Примеры использования API - Dubai Platform

## Обзор API

Dubai Platform предоставляет несколько API для различных компонентов системы. Каждый API имеет свои особенности и возможности.

## 🚀 Project Launcher API

### Основные endpoints

#### Health Check
```bash
## Проверка статуса сервиса
curl http://localhost:80/health

## Ответ
{
  "status": "healthy",
  "timestamp": "2025-01-16T22:00:00Z",
  "version": "2.0.0"
}
```

#### Управление проектами
```bash
## Получение списка всех проектов
curl http://localhost:80/api/v1/projects

## Запуск проекта
curl -X POST http://localhost:80/api/v1/projects/dxb-frontend/start

## Остановка проекта
curl -X POST http://localhost:80/api/v1/projects/dxb-frontend/stop

## Перезапуск проекта
curl -X POST http://localhost:80/api/v1/projects/dxb-frontend/restart
```

#### Мониторинг ресурсов
```bash
## Получение метрик системы
curl http://localhost:80/api/v1/monitoring/system

## Получение метрик конкретного проекта
curl http://localhost:80/api/v1/monitoring/projects/dxb-frontend

## Получение логов проекта
curl http://localhost:80/api/v1/projects/dxb-frontend/logs
```

### AI-driven endpoints

#### Получение AI инсайтов
```bash
## Анализ текущего состояния
curl http://localhost:80/api/v1/ai/insights/current

## Предсказание проблем
curl http://localhost:80/api/v1/ai/predictions/issues

## Рекомендации по оптимизации
curl http://localhost:80/api/v1/ai/recommendations/optimization
```

#### Автоматические действия
```bash
## Автоматическое масштабирование
curl -X POST http://localhost:80/api/v1/ai/actions/scale \
  -H "Content-Type: application/json" \
  -d '{"project": "dxb-frontend", "action": "scale_up"}'

## Self-healing
curl -X POST http://localhost:80/api/v1/ai/actions/heal \
  -H "Content-Type: application/json" \
  -d '{"project": "realty-backend"}'
```

## 🏠 DXB Frontend API

### Основные endpoints

#### Аутентификация
```bash
## Вход в систему
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

## Регистрация
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "password", "name": "New User"}'
```

#### Недвижимость
```bash
## Получение списка объектов недвижимости
curl http://localhost:3000/api/properties?page=1&limit=20

## Поиск недвижимости
curl "http://localhost:3000/api/properties/search?location=dubai&type=apartment&price_min=100000&price_max=500000"

## Получение деталей объекта
curl http://localhost:3000/api/properties/123

## Создание нового объекта
curl -X POST http://localhost:3000/api/properties \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Luxury Apartment",
    "location": "Dubai Marina",
    "price": 2500000,
    "type": "apartment",
    "bedrooms": 2,
    "bathrooms": 2
  }'
```

#### AI Ассистент
```bash
## Отправка вопроса AI ассистенту
curl -X POST http://localhost:3000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Какие районы в Дубае лучше всего подходят для инвестиций в недвижимость?",
    "context": "investment_advice"
  }'

## Получение истории чата
curl http://localhost:3000/api/ai/chat/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Аналитика
```bash
## Получение аналитики по районам
curl http://localhost:3000/api/analytics/districts

## Получение трендов цен
curl "http://localhost:3000/api/analytics/trends?period=6months&type=apartment"

## Получение ROI анализа
curl "http://localhost:3000/api/analytics/roi?district=dubai_marina&property_type=apartment"
```

## 🧠 Realty Backend API

### REST API

#### Основные endpoints
```bash
## Получение списка объектов недвижимости
curl http://localhost:8000/api/properties/

## Получение конкретного объекта
curl http://localhost:8000/api/properties/1/

## Создание объекта
curl -X POST http://localhost:8000/api/properties/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "New Property",
    "price": 1500000,
    "location": "Dubai Hills",
    "property_type": "apartment"
  }'

## Обновление объекта
curl -X PUT http://localhost:8000/api/properties/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "price": 1600000
  }'

## Удаление объекта
curl -X DELETE http://localhost:8000/api/properties/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Скрейпер API
```bash
## Запуск скрейпера
curl -X POST http://localhost:8000/api/scraper/start \
  -H "Authorization: Bearer YOUR_TOKEN"

## Статус скрейпера
curl http://localhost:8000/api/scraper/status

## Остановка скрейпера
curl -X POST http://localhost:8000/api/scraper/stop \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Отчеты API
```bash
## Генерация отчета по району
curl -X POST http://localhost:8000/api/reports/district/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "district": "Dubai Marina",
    "report_type": "market_analysis",
    "period": "6months"
  }'

## Получение готового отчета
curl http://localhost:8000/api/reports/123/download
```

### GraphQL API

#### Основные запросы
```graphql
## Запрос объектов недвижимости
query GetProperties($limit: Int, $offset: Int) {
  properties(limit: $limit, offset: $offset) {
    id
    title
    price
    location
    propertyType
    bedrooms
    bathrooms
    area
    createdAt
  }
}

## Запрос конкретного объекта
query GetProperty($id: ID!) {
  property(id: $id) {
    id
    title
    price
    location
    propertyType
    bedrooms
    bathrooms
    area
    description
    amenities
    images {
      url
      caption
    }
    createdAt
    updatedAt
  }
}

## Мутация создания объекта
mutation CreateProperty($input: PropertyInput!) {
  createProperty(input: $input) {
    property {
      id
      title
      price
      location
    }
    errors {
      field
      message
    }
  }
}
```

#### Переменные для GraphQL
```json
{
  "limit": 20,
  "offset": 0,
  "id": "1",
  "input": {
    "title": "Luxury Villa",
    "price": 5000000,
    "location": "Palm Jumeirah",
    "propertyType": "villa",
    "bedrooms": 4,
    "bathrooms": 5,
    "area": 450
  }
}
```

## 💾 Memory LLM API

### Основные endpoints

#### Health Check
```bash
## Проверка статуса
curl http://localhost:8080/health

## Ответ
{
  "status": "healthy",
  "timestamp": "2025-01-16T22:00:00Z",
  "version": "1.0.0"
}
```

#### Векторные операции
```bash
## Добавление документа в векторную базу
curl -X POST http://localhost:8080/api/v1/vectors/add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Luxury apartment in Dubai Marina with 2 bedrooms and 2 bathrooms",
    "metadata": {
      "property_id": "123",
      "location": "Dubai Marina",
      "type": "apartment"
    }
  }'

## Поиск похожих документов
curl -X POST http://localhost:8080/api/v1/vectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "apartment dubai marina",
    "limit": 10,
    "threshold": 0.7
  }'

## Удаление документа
curl -X DELETE http://localhost:8080/api/v1/vectors/123
```

#### Кэширование
```bash
## Получение кэшированного результата
curl http://localhost:8080/api/v1/cache/get?key=property_123

## Установка кэша
curl -X POST http://localhost:8080/api/v1/cache/set \
  -H "Content-Type: application/json" \
  -d '{
    "key": "property_123",
    "value": "property_data",
    "ttl": 3600
  }'

## Удаление кэша
curl -X DELETE http://localhost:8080/api/v1/cache/delete?key=property_123
```

## 🤖 AI Agents API

### CrewAI API
```bash
## Запуск маркетинговой команды
curl -X POST http://localhost:8001/api/crew/marketing/start \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Создать маркетинговую стратегию для недвижимости в Дубае",
    "context": "real_estate_marketing",
    "agents": ["researcher", "strategist", "copywriter"]
  }'

## Статус выполнения
curl http://localhost:8001/api/crew/marketing/status

## Результат работы
curl http://localhost:8001/api/crew/marketing/result
```

### LangGraph API
```bash
## SQL агент запрос
curl -X POST http://localhost:8002/api/langgraph/sql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Показать средние цены по районам",
    "database": "realty_db"
  }'

## Результат SQL запроса
curl http://localhost:8002/api/langgraph/sql/result
```

### ADK API
```bash
## Факт-чекинг
curl -X POST http://localhost:8003/api/adk/factcheck \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Цены на недвижимость в Дубае выросли на 15% в 2024 году",
    "context": "real_estate_prices"
  }'

## Результат проверки
curl http://localhost:8003/api/adk/factcheck/result
```

## 📊 Monitoring API

### Prometheus API
```bash
## Получение метрик
curl http://localhost:9090/api/v1/query?query=up

## Получение метрик за период
curl "http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[5m])&start=2025-01-16T00:00:00Z&end=2025-01-16T23:59:59Z&step=1m"

## Список targets
curl http://localhost:9090/api/v1/targets
```

### Grafana API
```bash
## Получение дашбордов
curl http://localhost:3003/api/dashboards \
  -H "Authorization: Bearer YOUR_GRAFANA_TOKEN"

## Получение конкретного дашборда
curl http://localhost:3003/api/dashboards/uid/dubai_platform \
  -H "Authorization: Bearer YOUR_GRAFANA_TOKEN"
```

## 🔐 Аутентификация

### JWT токены
```bash
## Получение токена
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'

## Использование токена
curl http://localhost:8000/api/properties/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### API ключи
```bash
## Использование API ключа
curl http://localhost:8000/api/properties/ \
  -H "X-API-Key: YOUR_API_KEY"
```

## 📝 Примеры использования

### Полный цикл работы с недвижимостью

#### 1. Создание объекта
```bash
## Создание объекта через REST API
curl -X POST http://localhost:8000/api/properties/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Luxury Apartment in Dubai Marina",
    "price": 2500000,
    "location": "Dubai Marina",
    "propertyType": "apartment",
    "bedrooms": 2,
    "bathrooms": 2,
    "area": 120,
    "description": "Beautiful apartment with marina view"
  }'
```

#### 2. Добавление в векторную базу
```bash
## Добавление описания в Memory LLM
curl -X POST http://localhost:8080/api/v1/vectors/add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Luxury Apartment in Dubai Marina with 2 bedrooms and 2 bathrooms, beautiful marina view, 120 sqm",
    "metadata": {
      "property_id": "456",
      "location": "Dubai Marina",
      "type": "apartment",
      "price_range": "2-3M"
    }
  }'
```

#### 3. Поиск похожих объектов
```bash
## Поиск через Memory LLM
curl -X POST http://localhost:8080/api/v1/vectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "apartment dubai marina 2 bedrooms marina view",
    "limit": 5,
    "threshold": 0.6
  }'
```

#### 4. Получение через Frontend API
```bash
## Получение объекта через Frontend API
curl http://localhost:3000/api/properties/456 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🚨 Обработка ошибок

### Стандартные HTTP коды
- **200**: Успешный запрос
- **201**: Создан новый ресурс
- **400**: Ошибка в запросе
- **401**: Не авторизован
- **403**: Доступ запрещен
- **404**: Ресурс не найден
- **500**: Внутренняя ошибка сервера

### Примеры ошибок
```json
{
  "error": "Validation failed",
  "details": {
    "price": ["Price must be positive"],
    "location": ["Location is required"]
  },
  "timestamp": "2025-01-16T22:00:00Z"
}
```

## 🔗 Полезные ссылки

- [Основная документация](../README.md)
- [API Overview](./overview.md)
- [Quick Start Guide](../deployment/quick-start.md)
- [Архитектура](../architecture/overview.md)

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка


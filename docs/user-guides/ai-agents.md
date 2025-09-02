# 🤖 AI Agents - Руководство пользователя

## Обзор AI агентов

Dubai Platform включает в себя множество AI агентов, построенных на различных фреймворках и технологиях. Каждый агент специализируется на определенных задачах и может работать как самостоятельно, так и в команде.

## 🏗️ Архитектура AI агентов

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agents Ecosystem                         │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Multi-Agent Systems                                       │
│  ├── A2A (Agent-to-Agent)                                     │
│  ├── CrewAI Marketing Team                                     │
│  ├── ADK Sock Shop                                             │
│  └── Embabel Travel Agent                                      │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Single Agent Systems                                      │
│  ├── Agno GitHub Analyzer                                      │
│  ├── LangGraph SQL Agent                                       │
│  ├── Spring AI Brave Search                                    │
│  └── Langchaingo DuckDuckGo                                    │
├─────────────────────────────────────────────────────────────────┤
│  🚀 Specialized Agents                                        │
│  ├── ADK Cerebras Golang Experts                               │
│  ├── Vercel AI-SDK Chat UI                                     │
│  └── Custom Agents                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Запуск AI агентов

### Предварительные требования

- **Docker Desktop** 4.43.0+ или **Docker Engine**
- **GPU** для локальных моделей (опционально)
- **API ключи** для внешних сервисов

### Быстрый запуск

#### 1. Клонирование репозитория
```bash
cd compose-for-agents
```

#### 2. Настройка переменных окружения
```bash
## Для каждого агента создайте .mcp.env файл
cp a2a/mcp.env.example a2a/.mcp.env

## Отредактируйте файл с вашими API ключами
nano a2a/.mcp.env
```

#### 3. Запуск агента
```bash
cd a2a
docker compose up --build
```

## 🤖 Multi-Agent Systems

### A2A (Agent-to-Agent) - Fact Checker

**Назначение**: Многоагентная система для проверки фактов

**Возможности**:
- Автоматическая проверка утверждений
- Использование DuckDuckGo для поиска информации
- Взаимодействие между агентами для анализа

**Запуск**:
```bash
cd a2a
cp mcp.env.example .mcp.env
## Настройте API ключи
docker compose up --build
```

**Использование**:
```bash
## Отправка запроса на проверку факта
curl -X POST http://localhost:8001/api/factcheck \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Цены на недвижимость в Дубае выросли на 15% в 2024 году",
    "context": "real_estate_market"
  }'
```

### CrewAI Marketing Team

**Назначение**: Команда агентов для создания маркетинговых стратегий

**Состав команды**:
- **Researcher** - исследователь рынка
- **Strategist** - стратег
- **Copywriter** - копирайтер

**Запуск**:
```bash
cd crew-ai
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Запуск маркетинговой кампании
curl -X POST http://localhost:8002/api/marketing/campaign \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Luxury Apartments in Dubai Marina",
    "target_audience": "High-net-worth individuals",
    "budget": "100000",
    "timeline": "3 months"
  }'
```

### ADK Sock Shop Agent

**Назначение**: Многоагентная система для управления интернет-магазином

**Возможности**:
- Управление товарами
- Обработка заказов
- Аналитика продаж
- Интеграция с MongoDB и Brave Search

**Запуск**:
```bash
cd adk-sock-shop
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Получение списка товаров
curl http://localhost:8003/api/products

## Создание заказа
curl -X POST http://localhost:8003/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "123",
    "items": [{"product_id": "1", "quantity": 2}],
    "shipping_address": "Dubai, UAE"
  }'
```

### Embabel Travel Agent

**Назначение**: Многоагентная система для планирования путешествий

**Возможности**:
- Поиск отелей и авиабилетов
- Планирование маршрутов
- Интеграция с погодными сервисами
- Поиск по Wikipedia и GitHub

**Запуск**:
```bash
cd embabel
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Планирование путешествия
curl -X POST http://localhost:8004/api/travel/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Dubai",
    "dates": "2025-02-01 to 2025-02-07",
    "budget": "5000",
    "preferences": ["luxury", "cultural", "shopping"]
  }'
```

## 🔍 Single Agent Systems

### Agno GitHub Issue Analyzer

**Назначение**: Анализ и обобщение GitHub issues

**Возможности**:
- Автоматический анализ issues
- Группировка по темам
- Приоритизация задач
- Интеграция с GitHub API

**Запуск**:
```bash
cd agno
cp mcp.env.example .mcp.env
## Настройте GitHub API ключ
docker compose up --build
```

**Использование**:
```bash
## Анализ issues репозитория
curl -X POST http://localhost:8005/api/github/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "dubai-project/platform",
    "analysis_type": "issue_summary"
  }'
```

### LangGraph SQL Agent

**Назначение**: Интеллектуальный SQL агент для работы с базами данных

**Возможности**:
- Генерация SQL запросов на естественном языке
- Анализ структуры базы данных
- Оптимизация запросов
- Интеграция с PostgreSQL

**Запуск**:
```bash
cd langgraph
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## SQL запрос на естественном языке
curl -X POST http://localhost:8006/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Показать средние цены на недвижимость по районам Дубая",
    "database": "realty_db"
  }'
```

### Spring AI Brave Search

**Назначение**: Поисковый агент с интеграцией Brave Search

**Возможности**:
- Поиск в интернете
- Анализ результатов
- Интеграция с Spring Framework
- Поддержка Java приложений

**Запуск**:
```bash
cd spring-ai
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Поиск информации
curl -X POST http://localhost:8007/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Dubai real estate market trends 2024",
    "max_results": 10
  }'
```

### Langchaingo DuckDuckGo

**Назначение**: Поисковый агент с интеграцией DuckDuckGo

**Возможности**:
- Анонимный поиск
- Интеграция с Go приложениями
- Быстрые результаты
- Отсутствие отслеживания

**Запуск**:
```bash
cd langchaingo
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Поиск через DuckDuckGo
curl -X POST http://localhost:8008/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Dubai property investment opportunities",
    "region": "ae"
  }'
```

## 🚀 Специализированные агенты

### ADK Cerebras Golang Experts

**Назначение**: Эксперты по Golang с интеграцией Cerebras AI

**Возможности**:
- Анализ Go кода
- Рекомендации по оптимизации
- Интеграция с Cerebras AI
- Локальные и удаленные модели

**Запуск**:
```bash
cd adk-cerebras
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Анализ Go кода
curl -X POST http://localhost:8009/api/golang/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "package main\n\nfunc main() {\n    fmt.Println(\"Hello, World!\")\n}",
    "analysis_type": "code_review"
  }'
```

### Vercel AI-SDK Chat UI

**Назначение**: Чат-интерфейс для смешивания MCPs и моделей

**Возможности**:
- Интеграция с различными MCPs
- Поддержка локальных моделей
- Wikipedia, Brave, Resend интеграции
- Современный UI

**Запуск**:
```bash
cd vercel
cp mcp.env.example .mcp.env
docker compose up --build
```

**Использование**:
```bash
## Отправка сообщения в чат
curl -X POST http://localhost:8010/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Расскажи о недвижимости в Дубае",
    "context": "real_estate_info",
    "mcp_services": ["wikipedia", "brave"]
  }'
```

## 🔧 Конфигурация агентов

### Переменные окружения

#### OpenAI API
```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
```

#### Anthropic API
```env
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-sonnet
```

#### GitHub API
```env
GITHUB_TOKEN=ghp-your-github-token
GITHUB_USERNAME=your-username
```

#### MongoDB
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=dubai_platform
```

### Docker конфигурация

#### Локальные модели
```yaml
## compose.yaml
services:
  agent:
    build: .
    environment:
      - MODEL_TYPE=local
      - LOCAL_MODEL_PATH=/models/qwen3
    volumes:
      - ./models:/models
```

#### OpenAI модели
```yaml
## compose.openai.yaml
services:
  agent:
    environment:
      - MODEL_TYPE=openai
      - OPENAI_API_KEY_FILE=/run/secrets/openai-api-key
    secrets:
      - openai-api-key
```

## 📊 Мониторинг агентов

### Health Checks
```bash
## Проверка статуса всех агентов
curl http://localhost:8001/health  # A2A
curl http://localhost:8002/health  # CrewAI
curl http://localhost:8003/health  # ADK Sock Shop
curl http://localhost:8004/health  # Embabel
curl http://localhost:8005/health  # Agno
curl http://localhost:8006/health  # LangGraph
curl http://localhost:8007/health  # Spring AI
curl http://localhost:8008/health  # Langchaingo
```

### Логи агентов
```bash
## Просмотр логов конкретного агента
docker logs -f a2a-agent
docker logs -f crewai-agent
docker logs -f adk-sock-shop-agent
```

### Метрики производительности
```bash
## Получение метрик агента
curl http://localhost:8001/metrics  # Prometheus метрики
curl http://localhost:8001/api/status  # Статус выполнения
```

## 🚨 Решение проблем

### Частые проблемы

#### 1. Агент не запускается
```bash
## Проверка логов
docker logs agent-name

## Проверка переменных окружения
docker exec -it agent-name env | grep API_KEY

## Перезапуск
docker compose restart agent-name
```

#### 2. Ошибки API ключей
```bash
## Проверка файла .mcp.env
cat .mcp.env

## Проверка в контейнере
docker exec -it agent-name cat /app/.mcp.env
```

#### 3. Проблемы с моделями
```bash
## Проверка доступности моделей
docker exec -it agent-name python -c "import torch; print(torch.cuda.is_available())"

## Переключение на OpenAI
docker compose -f compose.yaml -f compose.openai.yaml up
```

### Получение помощи

#### Логи и диагностика
```bash
## Сбор всех логов
docker logs --tail 100 a2a-agent > a2a.log
docker logs --tail 100 crewai-agent > crewai.log

## Проверка ресурсов
docker stats --no-stream
```

#### Полезные команды
```bash
## Полная перезагрузка
docker compose down
docker system prune -a
docker compose up --build

## Проверка версий
docker --version
docker compose version
```

## 🔗 Полезные ссылки

- [Основная документация](../README.md)
- [API документация](../api/examples.md)
- [Quick Start Guide](../deployment/quick-start.md)
- [Архитектура](../architecture/overview.md)

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка


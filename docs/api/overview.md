# 🚀 API Overview - Dubai Project

## Обзор API системы Dubai

### Основные компоненты API

#### 1. Frontend API (DXB-frontend-develop)
- **React + TypeScript** приложение
- **API endpoints** для управления недвижимостью
- **AI Assistant** интеграция
- **Мультиязычность** (EN, DE, RU)

#### 2. Backend Services
- **Java Memory LLM** - основная бизнес-логика
- **Realty Service** - управление недвижимостью
- **PFImport** - импорт данных
- **Project Launcher** - AI-driven управление проектами

#### 3. AI Agents (compose-for-agents)
- **ADK** - Agent Development Kit
- **Crew AI** - командная работа агентов
- **LangGraph** - графовые агенты
- **Spring AI** - Java AI интеграция

### Технологический стек

- **Frontend**: React, TypeScript, SCSS
- **Backend**: Java, Python, FastAPI
- **AI/ML**: OpenAI, Anthropic, Local LLM
- **Database**: MongoDB, SQLite, PostgreSQL
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, Docker Compose

### Архитектура API

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                      │
│  React + TypeScript + SCSS + AI Assistant             │
├─────────────────────────────────────────────────────────┤
│                    API Gateway                         │
│  Nginx + Load Balancer + Authentication               │
├─────────────────────────────────────────────────────────┤
│                    Backend Services                    │
│  Java Memory LLM + Realty + PFImport + Project Launcher│
├─────────────────────────────────────────────────────────┤
│                    AI Agents Layer                     │
│  ADK + Crew AI + LangGraph + Spring AI                │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                          │
│  MongoDB + SQLite + PostgreSQL + Vector DB            │
└─────────────────────────────────────────────────────────┘
```

### Основные функции API

1. **Управление недвижимостью**
   - CRUD операции с объектами
   - Аналитика и отчеты
   - Импорт данных

2. **AI и машинное обучение**
   - Анализ рынка недвижимости
   - Предсказание цен
   - Автоматические рекомендации

3. **Мониторинг и управление**
   - Health checks сервисов
   - Автоматическое масштабирование
   - Self-healing системы

### Аутентификация и безопасность

- **API Key** аутентификация
- **JWT токены** для сессий
- **Rate limiting** для защиты от DDoS
- **HTTPS** шифрование
- **CORS** настройки

### Документация по компонентам

- [Frontend API](./frontend-api.md)
- [Backend Services](./backend-services.md)
- [AI Agents](./ai-agents.md)
- [Database Schema](./database-schema.md)
- [Authentication](./authentication.md)
- [Examples](./examples.md)

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка

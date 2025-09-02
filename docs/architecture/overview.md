# 🏗️ Архитектура Dubai Platform

## Обзор системы

Dubai Platform - это комплексная экосистема для работы с недвижимостью, построенная на микросервисной архитектуре с интеграцией AI/ML технологий.

## 🏗️ Архитектурная схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dubai Platform                              │
├─────────────────────────────────────────────────────────────────┤
│  🚀 Project Launcher API Service                              │
│  ├── Управление проектами                                      │
│  ├── Мониторинг и метрики                                      │
│  ├── Автоматизация развертывания                               │
│  └── Централизованное логирование                              │
├─────────────────────────────────────────────────────────────────┤
│  🏠 DXB Frontend (React)                                      │
│  ├── AI Ассистент по недвижимости                              │
│  ├── Аналитические дашборды                                    │
│  ├── Многоязычность (EN/DE/RU)                                │
│  └── Responsive дизайн                                         │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Realty Backend (Django)                                   │
│  ├── REST + GraphQL API                                        │
│  ├── Аналитика рынка недвижимости                              │
│  ├── Скрейпер-модуль                                           │
│  └── Отчеты и метрики                                          │
├─────────────────────────────────────────────────────────────────┤
│  🤖 AI Agents & Frameworks                                    │
│  ├── A2A Multi-Agent Fact Checker                              │
│  ├── Agno GitHub Issue Analyzer                                │
│  ├── CrewAI Marketing Team                                     │
│  ├── LangGraph SQL Agent                                       │
│  └── Spring AI + DuckDuckGo                                    │
├─────────────────────────────────────────────────────────────────┤
│  💾 Memory LLM Service (Java)                                  │
│  ├── Векторные эмбеддинги                                      │
│  ├── PostgreSQL + pgvector                                     │
│  ├── Redis кэширование                                         │
│  └── REST API для интеграции                                   │
├─────────────────────────────────────────────────────────────────┤
│  📊 Monitoring & Analytics                                     │
│  ├── Prometheus метрики                                        │
│  ├── Grafana дашборды                                          │
│  ├── ELK Stack логирование                                     │
│  └── Health checks                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Основные компоненты

### 1. Project Launcher API Service
- **Назначение**: Централизованное управление всеми проектами
- **Технологии**: FastAPI, Python, Docker
- **Функции**: 
  - Запуск/остановка сервисов
  - Мониторинг ресурсов
  - Автоматическое масштабирование
  - Self-healing

### 2. DXB Frontend
- **Назначение**: Пользовательский интерфейс
- **Технологии**: React 18, TypeScript, SCSS
- **Функции**:
  - AI ассистент по недвижимости
  - Аналитические дашборды
  - Многоязычность (EN/DE/RU)
  - Responsive дизайн

### 3. Realty Backend
- **Назначение**: Основная бизнес-логика
- **Технологии**: Django 5.1, Python 3.12, GraphQL
- **Функции**:
  - REST + GraphQL API
  - Аналитика рынка недвижимости
  - Скрейпер-модуль
  - Отчеты и метрики

### 4. AI Agents Framework
- **Назначение**: Искусственный интеллект и автоматизация
- **Технологии**: CrewAI, LangGraph, Spring AI
- **Функции**:
  - Multi-agent системы
  - Автоматический анализ
  - Генерация контента
  - Принятие решений

### 5. Memory LLM Service
- **Назначение**: Векторная память и семантический поиск
- **Технологии**: Java, PostgreSQL + pgvector, Redis
- **Функции**:
  - Векторные эмбеддинги
  - Семантический поиск
  - Кэширование
  - REST API

### 6. Monitoring Stack
- **Назначение**: Мониторинг и аналитика
- **Технологии**: Prometheus, Grafana, ELK Stack
- **Функции**:
  - Сбор метрик
  - Визуализация данных
  - Анализ логов
  - Алерты

## 🔄 Потоки данных

### 1. Пользовательский поток
```
User → DXB Frontend → Realty Backend → Database
                ↓
            AI Assistant → Memory LLM → Vector DB
```

### 2. AI агенты поток
```
External Data → AI Agents → Memory LLM → Vector DB
                    ↓
            Realty Backend → Database
```

### 3. Мониторинг поток
```
All Services → Prometheus → Grafana → Alerts
                    ↓
            Project Launcher → Actions
```

## 🗄️ Базы данных

### PostgreSQL
- **Основная БД**: realty_main
- **Memory LLM БД**: memory_llm с pgvector
- **Пользователи**: postgres, memoryuser

### Redis
- **Кэширование**: Часто используемые данные
- **Сессии**: Пользовательские сессии
- **Очереди**: Асинхронные задачи

### SQLite
- **Локальная разработка**: pfimport-main
- **Тестирование**: Временные данные

## 🌐 Сетевая архитектура

### Порты и сервисы
- **80**: Project Launcher (основной)
- **3000**: DXB Frontend
- **8000**: Realty Backend
- **8080**: Memory LLM
- **3003**: Grafana
- **9090**: Prometheus
- **5601**: Kibana

### Docker сети
- **Default bridge**: Изоляция сервисов
- **Custom networks**: Для связанных сервисов
- **Port mapping**: Доступ извне контейнеров

## 🔒 Безопасность

### Аутентификация
- **JWT токены**: Для API доступа
- **API ключи**: Для внешних интеграций
- **Session management**: Для веб-интерфейса

### Авторизация
- **RBAC**: Role-based access control
- **Permission levels**: Разные уровни доступа
- **Audit logs**: Логирование всех действий

### Сетевая безопасность
- **HTTPS**: Шифрование трафика
- **Firewall**: Ограничение доступа
- **Rate limiting**: Защита от DDoS

## 📈 Масштабируемость

### Горизонтальное масштабирование
- **Load balancing**: Nginx reverse proxy
- **Auto-scaling**: На основе метрик
- **Service discovery**: Автоматическое обнаружение

### Вертикальное масштабирование
- **Resource limits**: Docker constraints
- **Memory optimization**: Redis кэширование
- **Database optimization**: Connection pooling

## 🔄 CI/CD и автоматизация

### GitHub Actions
- **Автоматические тесты**: Unit, integration, e2e
- **Автоматический деплой**: При push в main
- **Security scanning**: Проверка уязвимостей

### Docker
- **Multi-stage builds**: Оптимизация образов
- **Health checks**: Автоматическая проверка
- **Volume management**: Персистентные данные

## 🚨 Отказоустойчивость

### Self-healing
- **Health checks**: Автоматическая проверка
- **Auto-restart**: При сбоях
- **Fallback mechanisms**: Резервные варианты

### Backup и восстановление
- **Автоматические бэкапы**: Базы данных
- **Point-in-time recovery**: Восстановление состояния
- **Disaster recovery**: План восстановления

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка

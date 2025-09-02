# 🚀 Dubai Platform MVP - Релиз для продакшена

**Упрощенная версия платформы для быстрого запуска в продакшен**

## 🎯 MVP функционал

✅ **Парсер PropertyFinder** - сбор данных о недвижимости  
✅ **Алгоритмы обработки** - расчет метрик без AI  
✅ **React фронтенд** - отображение данных  
✅ **Авторизация** - регистрация и вход  
✅ **Payment заглушка** - имитация оплаты  

## 🏗️ Архитектура MVP

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Parser Service │    │   API Service   │    │    Frontend     │
│  (pfimport-main)│    │  (realty-main)  │    │ (DXB-frontend)  │
│     Port 8002   │    │    Port 8000    │    │    Port 3000    │
│     SQLite      │    │   PostgreSQL    │    │      React      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Nginx Proxy    │
                    │    Port 80      │
                    └─────────────────┘
```

## 🚀 Быстрый запуск

### 1. Запуск MVP
```bash
# Клонирование ветки MVP
git checkout mvp-release

# Запуск всех сервисов
docker compose -f docker-compose.mvp.yml up -d

# Проверка статуса
docker compose -f docker-compose.mvp.yml ps
```

### 2. Доступ к сервисам
- **Фронтенд**: http://localhost:3000
- **API**: http://localhost:8000  
- **Парсер**: http://localhost:8002
- **Прокси**: http://localhost:80

### 3. Мониторинг (опционально)
```bash
# Запуск с мониторингом
docker compose -f docker-compose.mvp.yml --profile monitoring up -d

# Доступ к мониторингу
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3003 (admin/admin)
```

## 📊 Управление данными

### Запуск парсера
```bash
# Парсинг 100 страниц PropertyFinder
docker compose -f docker-compose.mvp.yml exec parser-service \
  python manage.py scrape_properties 1 100

# Экспорт в shared-data
docker compose -f docker-compose.mvp.yml exec parser-service \
  python manage.py export_to_json /shared-data/
```

### Импорт в основную БД  
```bash
# Импорт из shared-data
docker compose -f docker-compose.mvp.yml exec api-service \
  python manage.py import_properties /shared-data/

# Пересчет метрик
docker compose -f docker-compose.mvp.yml exec api-service \
  python manage.py recalculate_reports --model building
```

## 🔧 MVP vs Full версия

### Что УБРАНО из MVP:
- ❌ AI агенты (CrewAI, LangGraph)
- ❌ Memory LLM сервис  
- ❌ Project Launcher
- ❌ Сложная автоматизация
- ❌ Advanced monitoring
- ❌ Machine Learning модели

### Что ОСТАВЛЕНО в MVP:
- ✅ Парсер данных PropertyFinder
- ✅ Алгоритмы расчета метрик  
- ✅ Django API (REST + GraphQL)
- ✅ React фронтенд с дашбордом
- ✅ Базовая авторизация
- ✅ PostgreSQL + Redis
- ✅ Nginx прокси

## 🎯 Roadmap для продакшена

### Неделя 1-2: Стабилизация
- [ ] Тестирование парсера на больших объемах
- [ ] Оптимизация алгоритмов обработки
- [ ] Подключение реальных данных к фронтенду

### Неделя 3-4: Интеграция  
- [ ] Авторизация фронт + бэк
- [ ] Payment заглушка
- [ ] API для всех данных

### Неделя 5-6: Production
- [ ] SSL/HTTPS настройка
- [ ] Production docker compose
- [ ] Smoke testing
- [ ] Go-live!

## 📞 Поддержка MVP

### Логи сервисов
```bash
# Все логи
docker compose -f docker-compose.mvp.yml logs -f

# Отдельные сервисы
docker logs mvp-parser
docker logs mvp-api  
docker logs mvp-frontend
```

### Остановка MVP
```bash
docker compose -f docker-compose.mvp.yml down
```

---

🎉 **MVP готов к разработке!** Фокус на **простоту и скорость релиза**.

**Возврат к Full версии**: `git checkout main` (когда понадобятся AI функции)
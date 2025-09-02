# 🚨 Решение общих проблем - Dubai Platform

## Частые проблемы и их решения

### 🔴 Проблемы с Docker

#### 1. Порт уже занят
**Симптомы**: Ошибка "port already in use" при запуске сервиса

**Решение**:
```bash
## Windows - проверка занятых портов
netstat -ano | findstr :3000

## Linux/Mac - проверка занятых портов
lsof -i :3000

## Остановка процесса
## Windows
taskkill /PID <PID> /F

## Linux/Mac
kill -9 <PID>
```

#### 2. Docker не запускается
**Симптомы**: Ошибка "Cannot connect to the Docker daemon"

**Решение**:
```bash
## Перезапуск Docker Desktop
## Windows: Restart Docker Desktop
## Linux: sudo systemctl restart docker

## Проверка статуса
docker info

## Очистка системы
docker system prune -a
docker volume prune
```

#### 3. Проблемы с образами
**Симптомы**: Ошибка "image not found" или поврежденные образы

**Решение**:
```bash
## Удаление поврежденных образов
docker rmi $(docker images -q)

## Пересборка образов
docker compose build --no-cache

## Очистка неиспользуемых образов
docker image prune -a
```

### 🔴 Проблемы с базами данных

#### 1. PostgreSQL не подключается
**Симптомы**: Ошибка "connection refused" или "authentication failed"

**Решение**:
```bash
## Проверка статуса контейнера
docker ps | grep postgres

## Просмотр логов
docker logs realty-main-db

## Перезапуск базы данных
docker restart realty-main-db

## Сброс базы данных (осторожно!)
docker volume rm realty_main_postgres_data
```

#### 2. Memory LLM база данных недоступна
**Симптомы**: Ошибка "pgvector extension not found"

**Решение**:
```bash
## Проверка правильного образа
docker images | grep pgvector

## Пересоздание контейнера
docker compose -f docker-compose.monitoring.yml down
docker compose -f docker-compose.monitoring.yml up -d

## Проверка расширений
docker exec -it memory-postgres-production psql -U memoryuser -d memory_llm -c "\dx"
```

### 🔴 Проблемы с сервисами

#### 1. Project Launcher не запускается
**Симптомы**: Ошибка "port 80 already in use" или сервис недоступен

**Решение**:
```bash
## Проверка порта 80
netstat -ano | findstr :80

## Запуск с другим портом
cd services/project-launcher
## Измените порт в docker-compose.yml
docker compose up -d

## Проверка логов
docker logs project-launcher
```

#### 2. DXB Frontend не отвечает
**Симптомы**: Белый экран или ошибки в консоли браузера

**Решение**:
```bash
## Проверка статуса
docker ps | grep dxb-frontend

## Перезапуск
docker restart dxb-frontend

## Просмотр логов
docker logs -f dxb-frontend

## Проверка переменных окружения
docker exec -it dxb-frontend env | grep NODE_ENV
```

#### 3. Realty Backend API недоступен
**Симптомы**: Ошибка "connection refused" или "timeout"

**Решение**:
```bash
## Проверка статуса
docker ps | grep realty-main

## Проверка health check
curl http://localhost:8000/health/

## Просмотр логов
docker logs realty-main-web

## Перезапуск
docker restart realty-main-web
```

### 🔴 Проблемы с AI агентами

#### 1. AI агенты не работают
**Симптомы**: Ошибки "model not found" или "API key invalid"

**Решение**:
```bash
## Проверка переменных окружения
cd compose-for-agents/adk
cat .env

## Проверка API ключей
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

## Перезапуск агентов
docker compose down
docker compose up -d
```

#### 2. Memory LLM не отвечает
**Симптомы**: Ошибка "vector search failed" или "embedding error"

**Решение**:
```bash
## Проверка статуса
docker ps | grep memory

## Проверка логов
docker logs memory-postgres-production

## Проверка подключения к базе
docker exec -it memory-postgres-production psql -U memoryuser -d memory_llm -c "SELECT 1;"

## Перезапуск
docker compose -f docker-compose.monitoring.yml restart
```

### 🔴 Проблемы с мониторингом

#### 1. Grafana недоступен
**Симптомы**: Ошибка "connection refused" или "login failed"

**Решение**:
```bash
## Проверка статуса
docker ps | grep grafana

## Проверка порта
netstat -ano | findstr :3003

## Перезапуск
docker restart grafana

## Проверка логов
docker logs grafana

## Сброс пароля (если нужно)
## По умолчанию: admin/admin
```

#### 2. Prometheus не собирает метрики
**Симптомы**: Нет данных в Grafana или ошибки "target down"

**Решение**:
```bash
## Проверка статуса
docker ps | grep prometheus

## Проверка конфигурации
docker exec -it prometheus cat /etc/prometheus/prometheus.yml

## Перезапуск
docker restart prometheus

## Проверка targets
curl http://localhost:9090/api/v1/targets
```

### 🔴 Проблемы с сетью

#### 1. Сервисы не видят друг друга
**Симптомы**: Ошибки "connection refused" между контейнерами

**Решение**:
```bash
## Проверка Docker сетей
docker network ls

## Проверка подключения контейнеров к сети
docker network inspect bridge

## Создание custom сети
docker network create dubai-network

## Подключение сервисов к сети
docker network connect dubai-network dxb-frontend
```

#### 2. Проблемы с DNS
**Симптомы**: Ошибки "name resolution failed"

**Решение**:
```bash
## Проверка DNS в контейнере
docker exec -it dxb-frontend nslookup google.com

## Настройка DNS в docker-compose
services:
  dxb-frontend:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

### 🔴 Проблемы с производительностью

#### 1. Высокое потребление CPU/RAM
**Симптомы**: Медленная работа системы или зависания

**Решение**:
```bash
## Проверка ресурсов
docker stats

## Ограничение ресурсов в docker-compose
services:
  dxb-frontend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

## Очистка неиспользуемых ресурсов
docker system prune -a
```

#### 2. Медленная работа базы данных
**Симптомы**: Долгие запросы или таймауты

**Решение**:
```bash
## Проверка размера базы
docker exec -it realty-main-db psql -U postgres -d realty -c "SELECT pg_size_pretty(pg_database_size('realty'));"

## Очистка старых данных
docker exec -it realty-main-db psql -U postgres -d realty -c "VACUUM ANALYZE;"

## Проверка индексов
docker exec -it realty-main-db psql -U postgres -d realty -c "\di"
```

## 🆘 Получение дополнительной помощи

### 1. Логи и диагностика
```bash
## Сбор всех логов
docker logs --tail 100 dxb-frontend > frontend.log
docker logs --tail 100 realty-main-web > backend.log
docker logs --tail 100 project-launcher > launcher.log

## Проверка системных ресурсов
docker system df
docker stats --no-stream
```

### 2. Health checks
```bash
## Проверка всех health endpoints
curl http://localhost:80/health
curl http://localhost:3000/health
curl http://localhost:8000/health/
curl http://localhost:8080/health
```

### 3. Полезные команды
```bash
## Полная перезагрузка системы
docker compose -f docker-compose.all-projects.yml down
docker system prune -a
docker compose -f docker-compose.all-projects.yml up -d

## Проверка версий
docker --version
docker compose version
docker version
```

## 🔗 Полезные ссылки

- [Основная документация](../README.md)
- [Quick Start Guide](../deployment/quick-start.md)
- [Архитектура](../architecture/overview.md)
- [API документация](../api/overview.md)

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка

## 🔴 Проблемы с API (Django Realty Backend)

### 1) /api/health/ возвращает 301 (редирект на https)
**Симптомы**: `HTTP/1.1 301 Moved Permanently`, `Location: https://localhost:8090/api/health/`

**Причина**: В прод-режиме `SECURE_SSL_REDIRECT=True` принудительно перенаправляет HTTP на HTTPS.

**Решения**:
```bash
# Локальный smoke без HTTPS (временно, только для диагностики)
# В docker-compose для api-service установите:
#   SECURE_SSL_REDIRECT=false

# Либо тестируйте с учётом редиректа
curl -i -L http://localhost:8090/api/health/

# Или обращайтесь сразу по https через Nginx/сертификат
curl -i https://<домен>/api/health/
```

### 2) ModuleNotFoundError: No module named 'rest_framework'
**Причина**: Отсутствуют зависимости DRF.

**Решение**:
```text
apps/realty-main/requirements.txt
djangorestframework
djangorestframework-simplejwt
```
Затем пересоберите образ и перезапустите сервис.

### 3) ImproperlyConfigured: The SECRET_KEY setting must not be empty
**Причина**: Не задан `SECRET_KEY` для Django.

**Решение**:
```bash
# В docker compose используйте переменную окружения SECRET_KEY или API_SECRET_KEY
# Пример (только для локалки):
API_SECRET_KEY=mvp-secret-key-change-in-production
```

### 4) Error loading psycopg_pool module / Did you install psycopg[pool]?
**Причина**: Не установлен пакет `psycopg` с extras.

**Решение**:
```text
apps/realty-main/requirements.txt
psycopg[binary,pool]==3.2.6
```
Пересоберите образ и перезапустите сервис.

### 5) Bind for 0.0.0.0:8000 failed: port is already allocated
**Причина**: Порт 8000 занят на хосте.

**Решение**:
```bash
# Используйте другой внешний порт, например 8090 → 8000
# В docker-compose:
#   ports:
#     - "${API_PORT:-8090}:8000"
# И экспортируйте переменную окружения перед запуском (PowerShell)
$env:API_PORT="8090"
```

### 6) Бесконечное ожидание базы / Database not ready
**Причина**: База не доступна/нет пароля, либо ещё не прошла healthcheck.

**Решение**:
```bash
# Убедитесь, что POSTGRES_PASSWORD задан, а depends_on использует healthcheck
# Перезапустите после готовности БД
```

### 7) CORS 403 / ошибки CORS в браузере
**Причина**: Отсутствуют нужные Origins/Hosts.

**Решение**:
```python
# apps/realty-main/realty/settings.py (читается из ENV)
DJANGO_ALLOWED_HOSTS = ["localhost","127.0.0.1","<домен>"]
CORS_ALLOWED_ORIGINS = [
  "http://localhost:3000",
  "http://localhost",
  "https://<домен>"
]
```

### 8) Smoke-тесты API
```bash
# Миграции и статика
docker compose -f docker-compose.prod.yml exec api-service \
  python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec api-service \
  python manage.py collectstatic --noinput

# Health (HTTP c редиректом)
curl -i -L http://localhost:8090/api/health/

# Health с CORS-проверкой
curl -i -H "Origin: http://localhost:3000" \
  http://localhost:8090/api/health/

# Базовый список API (если реализован)
curl -i http://localhost:8090/api/
```

### 9) Наличие health endpoint
`/api/health/` реализован в `realty/api/views.py` и подключён в `realty/api/urls.py`. 

### 10) PowerShell alias `curl` ломает команды
**Симптомы**: Странные ошибки `Get-Content: The input object cannot be bound...` при использовании пайпов (`| cat`).

**Решение**:
```powershell
# На Windows используйте системный curl.exe
curl.exe -s -i http://localhost:8002/health/

# Либо замените пайпы на простой вызов без перенаправления
docker compose -f docker-compose.prod.yml exec parser-service python manage.py migrate --noinput
```

### 11) Parser export: AttributeError на полях `is_verified`/`size`
**Симптомы**:
- `AttributeError: 'Property' object has no attribute 'is_verified'`
- `AttributeError: 'Property' object has no attribute 'size'`

**Причина**: В модели поля называются иначе (`verified`, `area_sqm/area_sqft`).

**Решение**: В `apps/pfimport-main/properties/management/commands/export_to_shared.py` использовать:
```python
verified = prop.verified
# sizeMin:
size_min = f"{prop.area_sqm} sqm" if prop.area_sqm else (f"{prop.area_sqft} sqft" if prop.area_sqft else "")
```
После правки пересобрать образ и повторить экспорт.

### 12) Parser: `no such table: properties_property` при экспорте
**Симптомы**: Ошибка при `export_to_shared` сразу после сборки контейнера.

**Решение**:
```bash
docker compose -f docker-compose.prod.yml exec parser-service python manage.py migrate --noinput
```

### 13) Симлинк в shared-data на Windows
**Симптомы**: Предупреждение про невозможность создать symlink `latest_export.json`.

**Решение**: Это ожидаемо на Windows без привилегий. Используйте сам файл `exported_properties_*.json` вместо симлинка.

### 14) API health: 404 на /api/health/
**Симптомы**: `404 Page not found` по `http://localhost:8000/api/health/`.

**Причина**: Health в проекте прокинут как `path("health/", MainView.as_view())` вне префикса `/api`.

**Решение**:
```bash
curl -i http://localhost:8000/health/
# либо через nginx
curl -i http://localhost/health
```

### 15) Порты и ENV
**Рекомендация**: придерживаться свободных портов с окончанием на `...90` и явно задавать переменные окружения перед запуском:
```powershell
$env:POSTGRES_PASSWORD="postgres"; $env:API_SECRET_KEY="dev"; $env:PARSER_SECRET_KEY="dev"
docker compose -f docker-compose.prod.yml up -d postgres redis api-service parser-service
```


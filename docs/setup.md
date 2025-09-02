# Руководство по установке

## Обзор

Пошаговое руководство по установке и настройке проекта Dubai.

## 📋 Предварительные требования

### Системные требования
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **RAM**: Минимум 8GB, рекомендуется 16GB
- **Storage**: Минимум 10GB свободного места
- **CPU**: Минимум 4 ядра

### Программное обеспечение
- **Python**: 3.8+
- **Node.js**: 16+
- **Java**: 11+ (для Memory LLM Service)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+

## 🚀 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/dubai-project.git
cd dubai-project
```

### 2. Запуск через Docker Compose
```bash
## Запуск всех сервисов
docker-compose up -d

## Проверка статуса
docker-compose ps
```

### 3. Проверка установки
```bash
## Проверка API
curl http://localhost:8000/api/health

## Проверка фронтенда
open http://localhost:3000
```

## 🔧 Детальная установка

### Установка Python зависимостей
```bash
## Создание виртуального окружения
python -m venv venv

## Активация окружения
## Windows
venv\Scripts\activate
## macOS/Linux
source venv/bin/activate

## Установка зависимостей
pip install -r requirements.txt
```

### Установка Node.js зависимостей
```bash
## Установка зависимостей
npm install

## Или с Yarn
yarn install
```

### Установка Java зависимостей
```bash
## Для Memory LLM Service
cd ai_services/memory_llm
./mvnw clean install
```

## 🐳 Docker установка

### Создание Docker образов
```bash
## Сборка всех образов
docker-compose build

## Сборка конкретного сервиса
docker-compose build real-estate-api
```

### Настройка переменных окружения
```bash
## Копирование примера
cp env/.env.example env/.env.local

## Редактирование переменных
nano env/.env.local
```

### Запуск сервисов
```bash
## Запуск в фоновом режиме
docker-compose up -d

## Просмотр логов
docker-compose logs -f

## Остановка сервисов
docker-compose down
```

## 🗄️ Настройка базы данных

### PostgreSQL
```bash
## Создание базы данных
docker exec -it dubai-postgres psql -U postgres
CREATE DATABASE dubai;
CREATE DATABASE dubai_ai;

## Применение миграций
python manage.py migrate
```

### Redis
```bash
## Проверка подключения
docker exec -it dubai-redis redis-cli ping

## Настройка пароля (опционально)
docker exec -it dubai-redis redis-cli
CONFIG SET requirepass your_password
```

## 🔐 Настройка аутентификации

### JWT токены
```bash
## Генерация секретного ключа
python -c "import secrets; print(secrets.token_urlsafe(32))"

## Добавление в .env
JWT_SECRET_KEY=your_generated_secret
```

### OpenAI API
```bash
## Получение API ключа
## https://platform.openai.com/api-keys

## Добавление в .env
OPENAI_API_KEY=your_openai_api_key
```

## 📊 Настройка мониторинга

### Prometheus
```bash
## Проверка метрик
curl http://localhost:9090/api/v1/targets

## Настройка алертов
cp monitoring/prometheus/alerts.example.yml monitoring/prometheus/alerts.yml
```

### Grafana
```bash
## Первый вход
## URL: http://localhost:3000
## Логин: admin
## Пароль: admin

## Импорт дашбордов
## См. monitoring/grafana/dashboards/
```

## 🧪 Тестирование установки

### Проверка API
```bash
## Health check
curl http://localhost:8000/api/health

## API документация
open http://localhost:8000/docs
```

### Проверка фронтенда
```bash
## Веб-приложение
open http://localhost:3000

## Админ панель
open http://localhost:3000/admin
```

### Проверка AI сервисов
```bash
## Memory LLM Service
curl http://localhost:8080/api/memory/health

## AI Gateway
curl http://localhost:8003/api/ai/health
```

## 🚨 Troubleshooting

### Частые проблемы

#### Порт уже занят
```bash
## Поиск процесса
netstat -ano | findstr :8000

## Остановка процесса
taskkill /PID <process_id> /F
```

#### Проблемы с Docker
```bash
## Перезапуск Docker
docker system prune -a
docker-compose down
docker-compose up -d
```

#### Проблемы с базой данных
```bash
## Сброс базы данных
docker-compose down -v
docker-compose up -d
```

#### Проблемы с зависимостями
```bash
## Очистка кэша
pip cache purge
npm cache clean --force

## Переустановка
pip install -r requirements.txt --force-reinstall
npm install --force
```

## 📚 Дополнительные ресурсы

### Документация
- [API Reference](./api/overview.md)
- [Database Schema](./database-schema.md)
- [Структура проекта](./PROJECT_STRUCTURE.md)

### Поддержка
- **GitHub Issues**: [Создать issue](https://github.com/your-username/dubai-project/issues)
- **Discussions**: [Форум](https://github.com/your-username/dubai-project/discussions)
- **Wiki**: [Документация](https://github.com/your-username/dubai-project/wiki)

## 🔄 Обновление

### Обновление кода
```bash
## Получение последних изменений
git pull origin main

## Обновление зависимостей
pip install -r requirements.txt --upgrade
npm update

## Перезапуск сервисов
docker-compose down
docker-compose up -d
```

### Обновление Docker образов
```bash
## Пересборка образов
docker-compose build --no-cache

## Обновление контейнеров
docker-compose up -d --force-recreate
```

---

**Статус**: Активный  
**Последнее обновление**: Август 2025


# 🏠 Real Estate Analytics Platform - MVP

Комплексная платформа для сбора, обработки и анализа данных о недвижимости в Дубае. Система объединяет данные из DLD (реальные сделки) и PropertyFinder для предоставления глубокой аналитики рынка недвижимости.

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Python 3.12+
- PostgreSQL 16+

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd realty-main
```

### 2. Создание файлов окружения

```bash
# Создаем .env для локальной разработки
cp .env.example .env
# Редактируем .env с вашими настройками
```

Пример `.env`:
```env
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/realty_db
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Запуск через Docker Compose

```bash
# Сборка и запуск локально (профиль backend)
docker compose --profile backend build
docker compose --profile backend up

# Production (рекомендуется для серверов)
docker compose -f docker-compose.production.yml up -d --build backend
```

### 4. Инициализация базы данных

```bash
# В новом терминале
docker compose exec realty-main-web python manage.py migrate --noinput
docker compose exec realty-main-web python manage.py createsuperuser
```

### 5. Healthcheck и статические файлы

```bash
# Проверка доступности API
curl http://localhost:8000/api/health/

# Сбор статических файлов (для прод)
docker compose exec realty-main-web python manage.py collectstatic --noinput
```

## 🏗️ Архитектура проекта

### Модули системы

1. **Скрейпер-модуль** (`scraper_module/`)
   - Автономные Python-скрипты для сбора данных с PropertyFinder
   - Bash-оркестратор `run_scraper.sh`
   - Автоматическая обработка и очистка данных

2. **Django Backend** (`realty/`)
   - **main**: Работа с данными DLD (реальные сделки)
   - **pfimport**: Импорт и агрегация данных PropertyFinder
   - **reports**: Генерация аналитических отчетов
   - **building_reports**: Отчеты по зданиям

3. **API Endpoints**
   - REST API: `/api/`
   - GraphQL API: `/graphql/`
   - Admin Panel: `/admin/`

### Технологический стек

- **Backend**: Django 4.2/5.1 (MVP Railway — 4.2), Python 3.12
- **Database**: PostgreSQL 16
- **API**: GraphQL (Strawberry), REST
- **Data Processing**: Pandas, NumPy
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Web Server**: Gunicorn (prod), runserver (dev)
- **Background Tasks**: django-tasks
- **Monitoring**: Prometheus Middleware (встроенный), опционально Sentry

## 📊 Основные возможности

### Аналитика по районам
- Средние цены продажи и аренды
- Количество сделок и зданий
- Динамика цен по времени

### Аналитика по зданиям
- ROI расчеты
- Дни на рынке
- Сравнение с рыночными показателями

### Аналитика по проектам
- Заполняемость
- Статистика по типам недвижимости
- Сравнение с конкурентами

### Рыночный обзор
- Общая статистика рынка
- Тренды цен и аренды
- Ликвидность активов

## 🔧 Разработка

### Локальная разработка

```bash
# Запуск с live reload
docker compose --profile local up

# Просмотр логов
docker compose --profile local logs -f web

# Выполнение команд Django
docker compose --profile local exec web python manage.py shell
```

### Структура кода

```
realty/
├── main/           # DLD данные и основные модели
├── pfimport/       # PropertyFinder импорт
├── reports/        # Аналитические отчеты
├── building_reports/ # Отчеты по зданиям
└── realty/         # Основные настройки Django
```

### GraphQL API

Откройте GraphQL Playground: `http://localhost:8000/graphql/`

Примеры запросов:

```graphql
# Общий обзор рынка
query MarketOverview {
  marketOverview {
    totalAreas
    totalBuildings
    totalProjects
    totalTransactions
    avgPrice
    avgRent
  }
}

# Аналитика по району
query AreaAnalytics($areaId: Int!) {
  areaAnalytics(areaId: $areaId) {
    area {
      nameEn
      nameAr
    }
    totalTransactions
    avgPrice
    avgRent
    buildingCount
  }
}
```

## 📈 Производительность

### Оптимизации

- ✅ Bulk операции для импорта данных
- ✅ Кэширование справочников в памяти
- ✅ Оптимизированные SQL запросы
- ✅ Предварительная агрегация метрик
- ✅ Индексы для быстрого поиска

### Мониторинг

- Sentry для отслеживания ошибок
- Django Debug Toolbar в development
- Health check endpoints

## 🚀 Развертывание

### Production

```bash
# Сборка production образа
docker compose --profile prod build

# Запуск production
docker compose --profile prod up -d

# Проверка статуса
docker compose --profile prod ps
```

### Ansible автоматизация

```bash
# Настройка сервера
ansible-playbook ansible/set_root.yml -l server_prod_realty -u root
ansible-playbook ansible/set_panchuk35.yml -l server_prod_realty -u panchuk35
ansible-playbook ansible/set_https_prod.yml -l server_prod_realty -u panchuk35
```

## 📝 Команды управления

### Django Management Commands

```bash
# Пересчет аналитических отчетов
python manage.py recalculate_reports --model building
python manage.py recalculate_reports --model area
python manage.py recalculate_reports --model citypf

# Импорт данных
python manage.py import_properties <directory>
python manage.py populate_db <csv_file>
```

### Скрипты скрейпера

```bash
# Запуск полного цикла
./run_scraper.sh

# Отдельные скрипты
python a_buy_improved.py    # Сбор данных о продаже
python a_improved.py        # Сбор данных об аренде
python take_all.py          # Обработка и объединение
```

## 🔒 Безопасность

- CSRF защита для всех форм
- Аутентификация через Django Allauth
- Безопасные настройки PostgreSQL
- HTTPS в production

## 📞 Поддержка

- **Документация**: См. `docs/` директорию
- **Issues**: GitHub Issues
- **Admin Panel**: `/admin/` для управления данными

## 🎯 Roadmap

### Фаза 1: Оптимизация производительности ✅
- [x] Оптимизация API запросов
- [x] Bulk операции для импорта
- [x] Рефакторинг Docker конфигурации

### Фаза 2: MVP функционал 🚧
- [ ] Регистрация и личный кабинет
- [ ] Система подписок (Stripe)
- [ ] Расширенная аналитика

### Фаза 3: Production готовность
- [ ] CI/CD pipeline
- [ ] Автоматические бэкапы
- [ ] Мониторинг и алерты

### Фаза 4: Расширение возможностей
- [ ] Мобильное приложение
- [ ] AI предсказания цен
- [ ] Интеграция с внешними API

---

**Версия**: MVP 1.0  
**Последнее обновление**: 2024  
**Лицензия**: Proprietary

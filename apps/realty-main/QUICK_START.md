# 🚀 Быстрый запуск проекта

## Предварительные требования

- Docker Desktop (Windows/Mac) или Docker + Docker Compose (Linux)
- Git

## Шаг 1: Клонирование проекта

```bash
git clone <repository-url>
cd realty-main
```

## Шаг 2: Запуск (выберите ваш ОС)

### Windows
```cmd
quick_start.bat
```

### Linux/Mac
```bash
chmod +x quick_start.sh
./quick_start.sh
```

### Ручной запуск
```bash
# Сборка и запуск
docker-compose build
docker-compose up -d

# Миграции
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser
```

## Шаг 3: Проверка работы

Откройте в браузере:
- **Главная страница**: http://localhost:8000/
- **Admin панель**: http://localhost:8000/admin/
- **GraphQL API**: http://localhost:8000/graphql/

## Шаг 4: Сбор данных (опционально)

```bash
cd scraper_module
./run_scraper.sh
```

## Шаг 5: Импорт данных

```bash
./auto_import.sh
```

## Полезные команды

```bash
# Просмотр логов
docker-compose logs -f web

# Остановка
docker-compose down

# Перезапуск
docker-compose restart web

# Django shell
docker-compose exec web python manage.py shell
```

## Устранение проблем

### Порт 8000 занят
```bash
# Остановите другие сервисы или измените порт в docker-compose.yml
```

### Проблемы с базой данных
```bash
# Перезапустите контейнеры
docker-compose down
docker-compose up -d
```

### Проблемы с правами доступа (Linux)
```bash
sudo chown -R $USER:$USER .
```

## Что дальше?

1. Изучите admin панель Django
2. Попробуйте GraphQL API
3. Запустите скрейпер для сбора данных
4. Импортируйте данные в систему

## Поддержка

Если что-то не работает:
1. Проверьте логи: `docker-compose logs web`
2. Убедитесь, что Docker запущен
3. Проверьте, что порты 8000 и 5432 свободны

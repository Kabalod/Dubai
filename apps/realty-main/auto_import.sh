#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Auto Import Script for Realty      ${NC}"
echo -e "${BLUE}========================================${NC}"

# Проверяем, что мы в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml не найден. Запустите скрипт из корневой директории проекта."
    exit 1
fi

# Проверяем, что Docker запущен
if ! docker info > /dev/null 2>&1; then
    log_error "Docker не запущен. Запустите Docker и попробуйте снова."
    exit 1
fi

# Проверяем статус контейнеров
log "Проверяем статус контейнеров..."
if ! docker compose --profile local ps | grep -q "Up"; then
    log_warning "Контейнеры не запущены. Запускаем..."
    docker compose --profile local up -d
    sleep 10  # Ждем запуска
fi

# Проверяем, что база данных доступна
log "Проверяем доступность базы данных..."
if ! docker compose --profile local exec db pg_isready -U postgres > /dev/null 2>&1; then
    log_error "База данных недоступна. Проверьте статус контейнеров."
    exit 1
fi

# Проверяем, что Django приложение работает
log "Проверяем статус Django приложения..."
if ! docker compose --profile local exec web python manage.py check > /dev/null 2>&1; then
    log_error "Django приложение не работает корректно."
    exit 1
fi

# Ищем директории с данными для импорта
log "Ищем данные для импорта..."
DATA_DIRS=()
for dir in scraped_data/scrape_*; do
    if [ -d "$dir" ]; then
        # Проверяем наличие JSON файлов
        if ls "$dir"/*.json > /dev/null 2>&1; then
            DATA_DIRS+=("$dir")
        fi
    fi
done

if [ ${#DATA_DIRS[@]} -eq 0 ]; then
    log_warning "Директории с данными не найдены. Запустите скрейпер сначала."
    echo -e "${YELLOW}Для запуска скрейпера выполните:${NC}"
    echo -e "  ${GREEN}cd scraper_module && ./run_scraper.sh${NC}"
    exit 1
fi

log "Найдено ${#DATA_DIRS[@]} директорий с данными:"
for dir in "${DATA_DIRS[@]}"; do
    echo -e "  📁 ${dir}"
done

# Спрашиваем пользователя о параметрах импорта
echo ""
echo -e "${BLUE}Параметры импорта:${NC}"
read -p "Очистить данные о продаже перед импортом? (y/N): " -n 1 -r
echo
WIPE_SALE=$([[ $REPLY =~ ^[Yy]$ ]] && echo "--wipe-sale" || echo "")

read -p "Очистить данные об аренде перед импортом? (y/N): " -n 1 -r
echo
WIPE_RENT=$([[ $REPLY =~ ^[Yy]$ ]] && echo "--wipe-rent" || echo "")

read -p "Очистить данные о районах перед импортом? (y/N): " -n 1 -r
echo
WIPE_AREA=$([[ $REPLY =~ ^[Yy]$ ]] && echo "--wipe-area" || echo "")

read -p "Очистить данные о зданиях перед импортом? (y/N): " -n 1 -r
echo
WIPE_BUILDING=$([[ $REPLY =~ ^[Yy]$ ]] && echo "--wipe-building" || echo "")

# Выполняем импорт для каждой директории
total_imported = 0
total_errors = 0

for dir in "${DATA_DIRS[@]}"; do
    log "Импортируем данные из $dir..."
    
    # Запускаем команду импорта
    if docker compose --profile local exec web python manage.py import_properties \
        "/app/$dir" $WIPE_SALE $WIPE_RENT $WIPE_AREA $WIPE_BUILDING; then
        
        total_imported=$((total_imported + 1))
        log "Успешно импортированы данные из $dir"
        
        # Очищаем флаги очистки после первого импорта
        WIPE_SALE=""
        WIPE_RENT=""
        WIPE_AREA=""
        WIPE_BUILDING=""
        
    else
        total_errors=$((total_errors + 1))
        log_error "Ошибка при импорте данных из $dir"
    fi
done

# Итоговая статистика
echo ""
echo -e "${BLUE}========================================${NC}"
if [ $total_errors -eq 0 ]; then
    echo -e "${GREEN}✅ Импорт завершен успешно!${NC}"
    echo -e "${GREEN}Импортировано директорий: $total_imported${NC}"
else
    echo -e "${YELLOW}⚠️  Импорт завершен с ошибками${NC}"
    echo -e "${GREEN}Успешно импортировано: $total_imported${NC}"
    echo -e "${RED}Ошибок: $total_errors${NC}"
fi

# Показываем ссылки на приложение
echo ""
echo -e "${BLUE}🌐 Доступные URL:${NC}"
echo -e "  ${GREEN}Главная страница:${NC} http://localhost:8000/"
echo -e "  ${GREEN}GraphQL API:${NC} http://localhost:8000/graphql/"
echo -e "  ${GREEN}Admin панель:${NC} http://localhost:8000/admin/"
echo -e "  ${GREEN}Health check:${NC} http://localhost:8000/health/"

# Показываем команды для управления
echo ""
echo -e "${BLUE}🔧 Полезные команды:${NC}"
echo -e "  ${GREEN}Просмотр логов:${NC} docker compose --profile local logs -f web"
echo -e "  ${GREEN}Django shell:${NC} docker compose --profile local exec web python manage.py shell"
echo -e "  ${GREEN}Пересчет отчетов:${NC} docker compose --profile local exec web python manage.py recalculate_reports --model building"

echo -e "${BLUE}========================================${NC}"

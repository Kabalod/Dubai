#!/bin/bash

# ========================================
# MVP Data Pipeline: Parser → API → Frontend
# Автоматический поток данных для MVP
# ========================================

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    MVP Data Pipeline                   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Параметры по умолчанию
PAGES_START=${1:-1}
PAGES_END=${2:-50}
IMPORT_CLEAN=${3:-false}

echo -e "${YELLOW}📋 Параметры пайплайна:${NC}"
echo -e "   Страницы: $PAGES_START - $PAGES_END"
echo -e "   Очистка данных: $IMPORT_CLEAN"
echo ""

# ========================================
# ШАГ 1: Запуск парсера
# ========================================
echo -e "${BLUE}🔍 ШАГ 1: Парсинг PropertyFinder${NC}"
echo -e "Запускаем парсер для страниц $PAGES_START-$PAGES_END..."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="properties_${TIMESTAMP}.json"

docker compose -f docker-compose.mvp.yml exec parser-service \
  python manage.py scrape_properties $PAGES_START $PAGES_END \
  --output "/shared-data/$OUTPUT_FILE" \
  --sleep 2

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Парсинг завершен: /shared-data/$OUTPUT_FILE${NC}"
else
    echo -e "${RED}❌ Ошибка парсинга${NC}"
    exit 1
fi

# ========================================
# ШАГ 2: Импорт в основную БД
# ========================================
echo ""
echo -e "${BLUE}📥 ШАГ 2: Импорт в PostgreSQL${NC}"

# Опции очистки
WIPE_FLAGS=""
if [ "$IMPORT_CLEAN" = "true" ]; then
    WIPE_FLAGS="--wipe-sale --wipe-rent --wipe-area --wipe-building"
    echo -e "${YELLOW}⚠️  Очищаем существующие данные${NC}"
fi

docker compose -f docker-compose.mvp.yml exec api-service \
  python manage.py import_properties "/shared-data/$OUTPUT_FILE" $WIPE_FLAGS

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Импорт завершен${NC}"
else
    echo -e "${RED}❌ Ошибка импорта${NC}"
    exit 1
fi

# ========================================
# ШАГ 3: Пересчет метрик
# ========================================
echo ""
echo -e "${BLUE}📊 ШАГ 3: Пересчет аналитики${NC}"

docker compose -f docker-compose.mvp.yml exec api-service \
  python manage.py recalculate_reports --model building

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Метрики пересчитаны${NC}"
else
    echo -e "${YELLOW}⚠️  Предупреждение при пересчете метрик${NC}"
fi

# ========================================
# ШАГ 4: Проверка данных на фронтенде
# ========================================
echo ""
echo -e "${BLUE}🌐 ШАГ 4: Проверка фронтенда${NC}"

# Получаем количество записей из API
API_COUNT=$(curl -s "http://localhost:8000/api/properties/count/" | jq -r '.count' 2>/dev/null || echo "0")

echo -e "Записей в базе: ${GREEN}$API_COUNT${NC}"

if [ "$API_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Данные доступны на фронтенде${NC}"
else
    echo -e "${YELLOW}⚠️  Данные не найдены, проверьте API${NC}"
fi

# ========================================
# ИТОГ
# ========================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Результат пайплайна                ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Парсер: $OUTPUT_FILE создан${NC}"
echo -e "${GREEN}✅ База данных: $API_COUNT записей${NC}"
echo -e "${GREEN}✅ Фронтенд: готов к использованию${NC}"
echo ""

echo -e "${YELLOW}🌐 Откройте приложение: http://localhost:80${NC}"
echo -e "${YELLOW}📊 Dashboard: http://localhost:3000${NC}"
echo -e "${YELLOW}🔧 API: http://localhost:8000/admin${NC}"
echo ""

# Показываем статистику
echo -e "${BLUE}📈 Быстрая статистика:${NC}"
docker compose -f docker-compose.mvp.yml exec api-service \
  python manage.py shell -c "
from realty.pfimport.models import PFListSale, PFListRent, Building, Area
print(f'Продажи: {PFListSale.objects.count()}')
print(f'Аренда: {PFListRent.objects.count()}') 
print(f'Здания: {Building.objects.count()}')
print(f'Районы: {Area.objects.count()}')
" 2>/dev/null || echo "Статистика недоступна"

echo ""
echo -e "${GREEN}🎉 MVP Data Pipeline завершен!${NC}"
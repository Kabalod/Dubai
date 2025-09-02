#!/bin/bash

# ========================================
# Dubai Platform MVP - Быстрый запуск
# ========================================

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Dubai Platform MVP - Запуск        ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker не запущен. Запустите Docker и попробуйте снова.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker работает${NC}"

# Проверка Docker Compose
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose не найден.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose работает${NC}"
echo ""

# Создаем shared-data директорию
mkdir -p shared-data
echo -e "${GREEN}✅ Создана shared-data директория${NC}"

# Запуск базовых сервисов
echo -e "${YELLOW}🚀 Запускаем базовые сервисы...${NC}"
docker compose -f docker-compose.mvp.yml up -d postgres redis

# Ждем готовности базы данных
echo -e "${YELLOW}⏳ Ждем готовности PostgreSQL...${NC}"
sleep 10

# Запуск приложений
echo -e "${YELLOW}🚀 Запускаем приложения...${NC}"
docker compose -f docker-compose.mvp.yml up -d api-service parser-service frontend

# Ждем готовности приложений
echo -e "${YELLOW}⏳ Ждем готовности приложений...${NC}"
sleep 15

# Nginx удалён - используем прямой доступ
echo -e "${YELLOW}🌐 Сервисы доступны напрямую:${NC}"
echo -e "${WHITE}   • Frontend: http://localhost:3000${NC}"
echo -e "${WHITE}   • Backend API: http://localhost:8000${NC}"

# Проверка статуса
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Статус сервисов MVP               ${NC}"
echo -e "${BLUE}========================================${NC}"

# Проверяем каждый сервис
check_service() {
    local service_name=$1
    local url=$2
    local description=$3
    
    if curl -f -s $url > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description: $url${NC}"
    else
        echo -e "${RED}❌ $description: $url${NC}"
    fi
}

check_service "postgres" "postgres://postgres:postgres@localhost:5432/dubai_realty" "PostgreSQL Database"
check_service "redis" "http://localhost:6379" "Redis Cache"
check_service "api" "http://localhost:8000" "Django API"
check_service "parser" "http://localhost:8002" "Parser Service"
check_service "frontend" "http://localhost:3000" "React Frontend"
# nginx удалён

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Доступные URL                      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🌐 Основное приложение: http://localhost:80${NC}"
echo -e "${GREEN}📊 React Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}🔧 Django API: http://localhost:8000${NC}"
echo -e "${GREEN}📡 Parser Service: http://localhost:8002${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Следующие шаги                     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}1. Откройте: http://localhost:80${NC}"
echo -e "${YELLOW}2. Запустите парсер: docker compose -f docker-compose.mvp.yml exec parser-service python manage.py scrape_properties 1 10${NC}"
echo -e "${YELLOW}3. Импортируйте данные: docker compose -f docker-compose.mvp.yml exec api-service python manage.py import_properties /shared-data/${NC}"
echo ""

echo -e "${GREEN}🎉 MVP запущен! Готов к разработке и тестированию.${NC}"
echo ""
echo -e "${BLUE}📚 Документация: README-MVP.md${NC}"
echo -e "${BLUE}🛑 Остановка: docker compose -f docker-compose.mvp.yml down${NC}"
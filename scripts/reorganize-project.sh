#!/bin/bash

# 🔄 Dubai Project - Реорганизация проекта
# Автоматическое перемещение существующих проектов в новую структуру

set -e

# Парсинг аргументов
DRY_RUN=false
FORCE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Неизвестный аргумент: $1"
            echo "Использование: $0 [--dry-run] [--force] [--verbose]"
            exit 1
            ;;
    esac
done

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Функции для вывода
print_header() {
    echo -e "\n${CYAN}🔄 $1${NC}"
    echo -e "${CYAN}$(printf '=%.0s' $(seq 1 $((${#1} + 4))))${NC}"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${WHITE}ℹ️  $1${NC}"
}

# План реорганизации
declare -A REORGANIZATION_PLAN
REORGANIZATION_PLAN=(
    ["realty-main"]="core/real_estate/realty:Основная логика недвижимости:core"
    ["pfimport-main"]="core/data_processing/pfimport:Импорт данных Property Finder:core"
    ["DXB-frontend-develop"]="frontend/dxb:React фронтенд приложение:frontend"
    ["Java_Memory_LLM-master"]="ai_services/memory/java-llm:Java LLM сервис памяти:ai"
    ["compose-for-agents"]="ai_services/agents/compose:Docker Compose для AI агентов:ai"
    ["services"]="infrastructure/services:Инфраструктурные сервисы:infrastructure"
    ["tools"]="tools:Инструменты разработки:tools"
    ["configs"]="infrastructure/configs:Конфигурационные файлы:infrastructure"
)

# Проверка существования папок
check_project_folders() {
    print_info "🔍 Проверка существующих проектов..."
    
    local existing_projects=()
    local missing_projects=()
    
    for project in "${!REORGANIZATION_PLAN[@]}"; do
        if [ -d "$project" ]; then
            existing_projects+=("$project")
            print_status "Найден: $project"
        else
            missing_projects+=("$project")
            print_warning "Отсутствует: $project"
        fi
    done
    
    echo ""
    print_info "Найдено проектов: ${#existing_projects[@]}"
    print_info "Отсутствует проектов: ${#missing_projects[@]}"
    
    echo "${existing_projects[@]}"
}

# Создание структуры папок
create_folder_structure() {
    print_info "📁 Создание структуры папок..."
    
    local folders=(
        "core/real_estate"
        "core/analytics"
        "core/data_processing"
        "ai_services/memory"
        "ai_services/agents"
        "ai_services/ml_models"
        "frontend"
        "infrastructure/docker"
        "infrastructure/monitoring"
        "infrastructure/deployment"
        "infrastructure/services"
        "infrastructure/configs"
        "tools"
        "scripts"
        "env"
        "logs"
    )
    
    for folder in "${folders[@]}"; do
        if [ ! -d "$folder" ]; then
            mkdir -p "$folder"
            print_status "Создана папка: $folder"
        else
            print_info "Папка уже существует: $folder"
        fi
    done
}

# Перемещение проекта
move_project() {
    local source="$1"
    local destination="$2"
    local description="$3"
    
    print_info "📦 Перемещение: $source → $destination"
    print_info "Описание: $description"
    
    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN: Проект НЕ будет перемещен"
        return
    fi
    
    # Проверка существования источника
    if [ ! -d "$source" ]; then
        print_error "Источник не найден: $source"
        return
    fi
    
    # Проверка существования назначения
    if [ -d "$destination" ]; then
        if [ "$FORCE" = true ]; then
            print_warning "Назначение существует, удаляем: $destination"
            rm -rf "$destination"
        else
            print_error "Назначение уже существует: $destination"
            print_info "Используйте --force для перезаписи"
            return
        fi
    fi
    
    # Создание родительской папки
    local parent_folder=$(dirname "$destination")
    if [ ! -d "$parent_folder" ]; then
        mkdir -p "$parent_folder"
    fi
    
    # Перемещение
    mv "$source" "$destination"
    print_status "Проект перемещен: $source → $destination"
    
    # Создание README в новой папке
    local readme_path="$destination/README.md"
    if [ ! -f "$readme_path" ]; then
        cat > "$readme_path" << EOF
# $description

Перемещен из: \`$source\`

## Описание
$description

## Статус
- ✅ Перемещен в новую структуру
- 📅 Дата: $(date +%d.%m.%Y)
- 🔄 Автоматически создано скриптом реорганизации

## Следующие шаги
1. Обновить конфигурации
2. Проверить зависимости
3. Обновить документацию
4. Протестировать функциональность
EOF
        print_status "Создан README: $readme_path"
    fi
}

# Создание Docker Compose файлов
create_docker_compose_files() {
    print_info "🐳 Создание Docker Compose файлов..."
    
    local compose_files=(
        "core:infrastructure/docker/docker-compose.core.yml:real-estate-api,analytics-service,data-processor:8000,8001,8002"
        "frontend:infrastructure/docker/docker-compose.frontend.yml:dxb-frontend,frontend-api:3000,3001"
        "infrastructure:infrastructure/docker/docker-compose.infrastructure.yml:postgres,redis,nginx:5432,6379,8080"
        "monitoring:infrastructure/docker/docker-compose.monitoring.yml:prometheus,grafana,elasticsearch,kibana:9090,3001,9200,5601"
    )
    
    for compose_config in "${compose_files[@]}"; do
        IFS=':' read -r type file_path services ports <<< "$compose_config"
        
        if [ ! -f "$file_path" ]; then
            local first_port=$(echo "$ports" | cut -d',' -f1)
            
            mkdir -p "$(dirname "$file_path")"
            
            cat > "$file_path" << EOF
version: '3.8'

services:
$(echo "$services" | tr ',' '\n' | while read -r service; do
    echo "  $service:"
    echo "    image: nginx:alpine"
    echo "    container_name: dubai-$service"
    echo "    ports:"
    echo "      - \"$first_port:80\""
    echo "    volumes:"
    echo "      - ./logs:/var/log/nginx"
    echo "    restart: unless-stopped"
    echo ""
done)

networks:
  default:
    name: dubai-$type-network
EOF
            
            print_status "Создан Docker Compose: $file_path"
        else
            print_info "Docker Compose уже существует: $file_path"
        fi
    done
}

# Создание переменных окружения
create_environment_files() {
    print_info "🔐 Создание файлов переменных окружения..."
    
    # Development environment
    local dev_env_file="env/.env.development"
    if [ ! -f "$dev_env_file" ]; then
        mkdir -p "$(dirname "$dev_env_file")"
        cat > "$dev_env_file" << 'EOF'
# Development Environment
NODE_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dubai_dev
DB_USER=dubai_user
DB_PASSWORD=dubai_pass

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Frontend
FRONTEND_PORT=3000
FRONTEND_API_URL=http://localhost:8000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
EOF
        print_status "Создан файл окружения: $dev_env_file"
    fi
    
    # Production environment
    local prod_env_file="env/.env.production"
    if [ ! -f "$prod_env_file" ]; then
        mkdir -p "$(dirname "$prod_env_file")"
        cat > "$prod_env_file" << 'EOF'
# Production Environment
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=dubai_prod
DB_USER=dubai_user
DB_PASSWORD=dubai_pass

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Frontend
FRONTEND_PORT=3000
FRONTEND_API_URL=http://api-gateway:8000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
EOF
        print_status "Создан файл окружения: $prod_env_file"
    fi
}

# Основная функция
main() {
    print_header "Dubai Project - Реорганизация"
    echo -e "${YELLOW}Режим: $([ "$DRY_RUN" = true ] && echo 'DRY RUN' || echo 'РЕАЛЬНОЕ ПЕРЕМЕЩЕНИЕ')${NC}"
    echo -e "${YELLOW}Принудительно: $([ "$FORCE" = true ] && echo 'Да' || echo 'Нет')${NC}"
    echo -e "${YELLOW}Подробно: $([ "$VERBOSE" = true ] && echo 'Да' || echo 'Нет')${NC}"
    
    # Проверка существующих проектов
    local existing_projects
    IFS=' ' read -ra existing_projects <<< "$(check_project_folders)"
    
    if [ ${#existing_projects[@]} -eq 0 ]; then
        print_error "Не найдено проектов для реорганизации"
        exit 1
    fi
    
    # Создание структуры папок
    create_folder_structure
    
    # Перемещение проектов
    print_header "Перемещение проектов"
    
    for project in "${existing_projects[@]}"; do
        local project_info="${REORGANIZATION_PLAN[$project]}"
        IFS=':' read -r destination description type <<< "$project_info"
        
        move_project "$project" "$destination" "$description"
        echo ""
    done
    
    # Создание Docker Compose файлов
    create_docker_compose_files
    
    # Создание файлов окружения
    create_environment_files
    
    # Финальный отчет
    print_header "Реорганизация завершена"
    print_status "Проект реорганизован в новую структуру"
    
    if [ "$DRY_RUN" = true ]; then
        print_warning "Это был DRY RUN - никакие изменения не были внесены"
        print_info "Запустите скрипт без --dry-run для реального перемещения"
    fi
    
    echo ""
    echo -e "${CYAN}📚 Следующие шаги:${NC}"
    echo "1. Проверьте новую структуру папок"
    echo "2. Обновите конфигурации и зависимости"
    echo "3. Протестируйте функциональность"
    echo "4. Обновите документацию"
    echo "5. Используйте project-manager.sh для управления"
}

# Запуск
main

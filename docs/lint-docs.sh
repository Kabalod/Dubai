#!/bin/bash

# 🚀 Dubai Project - Lint Documentation
# Простой скрипт для проверки качества документации

set -e

echo "🔍 Проверка документации Dubai Project..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка наличия markdownlint
check_markdownlint() {
    if command -v markdownlint &> /dev/null; then
        print_status "Markdownlint найден"
        return 0
    else
        print_warning "Markdownlint не найден. Установите: npm install -g markdownlint-cli"
        return 1
    fi
}

# Проверка markdown файлов
lint_markdown() {
    if check_markdownlint; then
        echo "📝 Проверка Markdown файлов..."
        markdownlint '**/*.md' --ignore .markdownlintignore
        print_status "Markdown линтинг завершен"
    else
        print_warning "Пропускаем Markdown линтинг"
    fi
}

# Проверка структуры заголовков
check_headers() {
    echo "🏷️  Проверка структуры заголовков..."
    
    # Проверка на множественные H1 заголовки
    h1_count=$(grep -r "^# " . --include="*.md" | wc -l)
    if [ "$h1_count" -gt 0 ]; then
        print_warning "Найдено $h1_count H1 заголовков (должен быть только один на файл)"
        grep -r "^# " . --include="*.md" | head -5
    fi
    
    # Проверка на пропущенные уровни заголовков
    echo "🔍 Проверка иерархии заголовков..."
    for file in $(find . -name "*.md" -not -path "./site/*"); do
        if [ -f "$file" ]; then
            # Простая проверка на H1 -> H3 (пропущен H2)
            if grep -q "^### " "$file" && ! grep -q "^## " "$file"; then
                print_warning "Файл $file: найден H3 без H2"
            fi
        fi
    done
}

# Проверка ссылок
check_links() {
    echo "🔗 Проверка внутренних ссылок..."
    
    # Поиск потенциально сломанных ссылок
    broken_links=0
    
    for file in $(find . -name "*.md" -not -path "./site/*"); do
        if [ -f "$file" ]; then
            # Поиск относительных ссылок
            while IFS= read -r line; do
                if [[ $line =~ \[([^\]]+)\]\(([^)]+)\) ]]; then
                    link="${BASH_REMATCH[2]}"
                    if [[ $link =~ ^\./ ]]; then
                        target_file=$(dirname "$file")/${link#./}
                        if [ ! -f "$target_file" ]; then
                            print_warning "Сломанная ссылка в $file: $link"
                            ((broken_links++))
                        fi
                    fi
                fi
            done < "$file"
        fi
    done
    
    if [ $broken_links -eq 0 ]; then
        print_status "Все внутренние ссылки корректны"
    else
        print_warning "Найдено $broken_links потенциально сломанных ссылок"
    fi
}

# Проверка структуры файлов
check_structure() {
    echo "📁 Проверка структуры документации..."
    
    required_files=(
        "README.md"
        "OVERVIEW.md"
        "NAVIGATION.md"
        "CONTRIBUTING.md"
        "GPT_RULES.md"
        "CURSOR_RULES.md"
    )
    
    missing_files=0
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Отсутствует обязательный файл: $file"
            ((missing_files++))
        fi
    done
    
    if [ $missing_files -eq 0 ]; then
        print_status "Структура документации корректна"
    else
        print_warning "Отсутствует $missing_files обязательных файлов"
    fi
}

# Основная функция
main() {
    echo "🚀 Запуск проверки документации..."
    echo "=================================="
    
    # Проверки
    check_structure
    lint_markdown
    check_headers
    check_links
    
    echo "=================================="
    print_status "Проверка документации завершена!"
    
    echo ""
    echo "📚 Следующие шаги:"
    echo "1. Исправьте найденные проблемы"
    echo "2. Запустите скрипт снова для проверки"
    echo "3. Следуйте правилам из CONTRIBUTING.md"
    echo "4. Используйте GPT_RULES.md для AI моделей"
    echo "5. Используйте CURSOR_RULES.md для Cursor IDE"
}

# Запуск
main "$@"

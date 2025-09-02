#!/bin/bash

echo "🚀 Запуск Real Estate Analytics Platform..."

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Создаем .env если его нет
if [ ! -f ".env" ]; then
    echo "📝 Создаем .env файл..."
    cat > .env << EOF
DEBUG=True
DATABASE_URL=postgres://postgres:postgres@db:5432/realty_db
SECRET_KEY=your-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
    echo "✅ .env файл создан"
fi

# Создаем .env.prod если его нет
if [ ! -f ".env.prod" ]; then
    echo "📝 Создаем .env.prod файл..."
    cat > .env.prod << EOF
DEBUG=False
DATABASE_URL=postgres://postgres:postgres@db:5432/realty_db
SECRET_KEY=your-production-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
    echo "✅ .env.prod файл создан"
fi

echo "🔨 Собираем Docker образы..."
docker-compose --profile local build

echo "🚀 Запускаем сервисы..."
docker-compose --profile local up -d

echo "⏳ Ждем запуска сервисов..."
sleep 15

echo "🗄️  Проверяем базу данных..."
if docker-compose --profile local exec db pg_isready -U postgres; then
    echo "✅ База данных готова"
else
    echo "❌ Проблема с базой данных"
    exit 1
fi

echo "🐍 Выполняем миграции Django..."
docker-compose --profile local exec web python manage.py migrate

echo "👤 Создаем суперпользователя..."
echo "Введите данные для суперпользователя:"
read -p "Username: " username
read -p "Email: " email
read -s -p "Password: " password
echo

docker-compose --profile local exec web python manage.py createsuperuser --noinput --username "$username" --email "$email"
docker-compose --profile local exec web python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='$username'); u.set_password('$password'); u.save()"

echo ""
echo "🎉 Проект успешно запущен!"
echo ""
echo "🌐 Доступные URL:"
echo "  📊 Главная страница: http://localhost:8000/"
echo "  🔍 GraphQL API: http://localhost:8000/graphql/"
echo "  ⚙️  Admin панель: http://localhost:8000/admin/"
echo "  💚 Health check: http://localhost:8000/health/"
echo ""
echo "🔧 Полезные команды:"
echo "  Просмотр логов: docker-compose --profile local logs -f web"
echo "  Остановка: docker-compose --profile local down"
echo "  Перезапуск: docker-compose --profile local restart web"
echo ""
echo "📚 Следующие шаги:"
echo "  1. Откройте http://localhost:8000/admin/ и войдите с созданными учетными данными"
echo "  2. Для сбора данных запустите: cd scraper_module && ./run_scraper.sh"
echo "  3. Для импорта данных: ./auto_import.sh"
echo ""
echo "✅ Готово к работе!"

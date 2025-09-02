@echo off
echo 🚀 Запуск Real Estate Analytics Platform...

REM Проверяем Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен. Установите Docker Desktop и попробуйте снова.
    pause
    exit /b 1
)

REM Создаем .env если его нет
if not exist ".env" (
    echo 📝 Создаем .env файл...
    (
        echo DEBUG=True
        echo DATABASE_URL=postgres://postgres:postgres@db:5432/realty_db
        echo SECRET_KEY=your-secret-key-change-this-in-production
        echo ALLOWED_HOSTS=localhost,127.0.0.1
    ) > .env
    echo ✅ .env файл создан
)

echo 🔨 Собираем Docker образы...
docker-compose build

echo 🚀 Запускаем сервисы...
docker-compose up -d

echo ⏳ Ждем запуска сервисов...
timeout /t 15 /nobreak >nul

echo 🗄️ Проверяем базу данных...
docker-compose exec db pg_isready -U postgres
if errorlevel 1 (
    echo ❌ Проблема с базой данных
    pause
    exit /b 1
)

echo 🐍 Выполняем миграции Django...
docker-compose exec web python manage.py migrate

echo 👤 Создаем суперпользователя...
set /p username="Username: "
set /p email="Email: "
set /p password="Password: "

docker-compose exec web python manage.py createsuperuser --noinput --username "%username%" --email "%email%"
docker-compose exec web python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='%username%'); u.set_password('%password%'); u.save()"

echo.
echo 🎉 Проект успешно запущен!
echo.
echo 🌐 Доступные URL:
echo   📊 Главная страница: http://localhost:8000/
echo   🔍 GraphQL API: http://localhost:8000/graphql/
echo   ⚙️ Admin панель: http://localhost:8000/admin/
echo   💚 Health check: http://localhost:8000/health/
echo.
echo 🔧 Полезные команды:
echo   Просмотр логов: docker-compose logs -f web
echo   Остановка: docker-compose down
echo   Перезапуск: docker-compose restart web
echo.
echo 📚 Следующие шаги:
echo   1. Откройте http://localhost:8000/admin/ и войдите с созданными учетными данными
echo   2. Для сбора данных запустите: cd scraper_module ^&^& run_scraper.sh
echo   3. Для импорта данных: auto_import.sh
echo.
echo ✅ Готово к работе!
pause

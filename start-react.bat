@echo off
echo ========================================
echo    React Frontend Launcher
echo    Запуск React приложения
echo ========================================
echo.

cd DXB-frontend-develop
echo Текущая папка: %CD%
echo.

if exist package.json (
    echo ✅ package.json найден!
    echo.
    echo 🚀 Запускаем React Frontend...
    echo Порт: 5173
    echo URL: http://localhost:5173
    echo.
    echo Нажмите Ctrl+C для остановки
    echo.
    npm run dev
) else (
    echo ❌ package.json не найден!
    echo Убедитесь, что вы находитесь в корневой папке проекта
    pause
)

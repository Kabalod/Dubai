@echo off
echo ========================================
echo    Real Estate Analytics Platform
echo    Автозапуск всех сервисов
echo ========================================
echo.

echo [1/4] Запуск Property Analyzer (порт 8001)...
start "Property Analyzer" cmd /k "cd pfimport-main && venv\Scripts\python manage.py runserver 127.0.0.1:8001"
timeout /t 3 /nobreak >nul

echo [2/4] Запуск React Frontend (порт 5173)...
start "React Frontend" cmd /k "cd DXB-frontend-develop && npm run dev"
timeout /t 3 /nobreak >nul

echo [3/4] Запуск HTTP Server (порт 3000)...
start "HTTP Server" cmd /k "python -m http.server 3000"
timeout /t 3 /nobreak >nul

echo [4/4] Проверка статуса...
echo.
echo ========================================
echo    Статус сервисов:
echo ========================================
echo Django Backend:     http://localhost:8000
echo Property Analyzer:  http://localhost:8001
echo React Frontend:     http://localhost:5173
echo HTTP Server:        http://localhost:3000
echo Dashboard:          http://localhost:3000/dashboard.html
echo ========================================
echo.
echo Все сервисы запущены! Откройте дашборд:
echo http://localhost:3000/dashboard.html
echo.
pause

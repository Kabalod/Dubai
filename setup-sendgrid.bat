@echo off
echo 🚀 Настройка SendGrid для отправки OTP
echo ======================================
echo.

echo 📋 Инструкции:
echo 1. Зарегистрируйтесь на https://sendgrid.com/
echo 2. Создайте и верифицируйте Sender Identity
echo 3. Получите API ключ с правами Mail Send
echo 4. Запустите этот скрипт снова с параметрами
echo.

if "%1"=="" (
    echo 💡 Использование:
    echo setup-sendgrid.bat "SG.ваш-api-ключ" "ваш-verified-email@domain.com"
    echo.
    echo Пример:
    echo setup-sendgrid.bat "SG.abc123..." "noreply@mydomain.com"
    goto :end
)

if "%2"=="" (
    echo ❌ Ошибка: Укажите оба параметра
    echo setup-sendgrid.bat "API_KEY" "FROM_EMAIL"
    goto :end
)

set SENDGRID_KEY=%1
set FROM_EMAIL=%2

echo 🔧 Настройка переменных окружения...
echo SENDGRID_API_KEY=%SENDGRID_KEY%> .env
echo DEFAULT_FROM_EMAIL=Dubai Real Estate ^<%FROM_EMAIL%^>>> .env

echo.
echo ✅ Создан файл .env с настройками:
type .env

echo.
echo 🔄 Перезапуск бекенда...
docker compose down realty-main-web
docker compose --profile backend up -d

echo.
echo 🧪 Тестирование отправки...
timeout /t 3 > nul
echo Отправляем тестовый OTP...

powershell -Command "Invoke-WebRequest -Uri http://localhost:8000/api/auth/send-otp/ -Method POST -ContentType 'application/json' -Body '{\"email\": \"%FROM_EMAIL%\"}'"

echo.
echo ✅ Готово! Проверьте почту %FROM_EMAIL%

:end
pause

@echo off
chcp 65001 > nul
echo.
echo 🚀 БЫСТРАЯ НАСТРОЙКА SENDGRID
echo ============================
echo.

if "%1"=="" (
    echo 📋 Этот скрипт поможет настроить SendGrid за 2 минуты!
    echo.
    echo 💡 Использование:
    echo quick-setup-sendgrid.bat "SG.ваш-api-ключ" "ваш-verified-email@domain.com"
    echo.
    echo 📚 Если у вас еще нет SendGrid аккаунта:
    echo 1. Откройте SENDGRID_ПОЛНАЯ_ИНСТРУКЦИЯ.md
    echo 2. Следуйте шагам 1-3 для получения API ключа
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    goto :end
)

if "%2"=="" (
    echo ❌ Ошибка: Укажите оба параметра
    echo.
    echo Пример:
    echo quick-setup-sendgrid.bat "SG.abc123..." "myemail@gmail.com"
    echo.
    pause
    goto :end
)

set API_KEY=%~1
set FROM_EMAIL=%~2

echo 🔧 Создание файла .env...
echo # SendGrid настройки> .env
echo SENDGRID_API_KEY=%API_KEY%>> .env
echo DEFAULT_FROM_EMAIL=Dubai Real Estate ^<%FROM_EMAIL%^>>> .env

echo.
echo ✅ Создан файл .env:
echo --------------------------------
type .env
echo --------------------------------
echo.

echo 🔄 Перезапуск бекенда с новыми настройками...
docker compose down realty-main-web
timeout /t 2 > nul
docker compose --profile backend up -d

echo.
echo ⏳ Ожидание запуска сервера...
timeout /t 5 > nul

echo.
echo 🔍 Проверка настроек в логах:
docker compose logs realty-main-web --tail 15 | findstr /C:"📧" /C:"✅" /C:"SendGrid"

echo.
echo 🧪 ТЕСТИРОВАНИЕ ОТПРАВКИ...
echo Отправляем тестовый OTP на %FROM_EMAIL%...
echo.

powershell -Command "$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/send-otp/' -Method POST -ContentType 'application/json' -Body '{\"email\": \"%FROM_EMAIL%\"}' -ErrorAction SilentlyContinue; if ($response) { Write-Host '✅ Запрос отправлен успешно:'; $response.Content } else { Write-Host '❌ Ошибка при отправке запроса' }"

echo.
echo 🎯 РЕЗУЛЬТАТ:
echo ============
echo ✅ Если все настроено правильно:
echo    - В логах выше должно быть: "✅ Email успешно отправлен"
echo    - На почту %FROM_EMAIL% придет письмо с OTP кодом
echo.
echo ❌ Если есть ошибки:
echo    - Проверьте что email %FROM_EMAIL% верифицирован в SendGrid
echo    - Убедитесь что API ключ правильный и имеет права Mail Send
echo    - Откройте SENDGRID_ПОЛНАЯ_ИНСТРУКЦИЯ.md для диагностики
echo.
echo 🌐 Теперь можете тестировать регистрацию на:
echo    http://localhost:3000/auth
echo.

pause

:end

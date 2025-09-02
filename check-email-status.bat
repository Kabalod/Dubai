@echo off
chcp 65001 > nul
echo.
echo 📧 ПРОВЕРКА СТАТУСА EMAIL СИСТЕМЫ
echo =================================

echo.
echo 🔍 1. Проверка файла .env:
if exist .env (
    echo ✅ Файл .env найден:
    echo --------------------------------
    type .env
    echo --------------------------------
) else (
    echo ❌ Файл .env не найден!
    echo 💡 Создайте .env с настройками SendGrid
)

echo.
echo 🔍 2. Проверка настроек в контейнере:
docker compose exec realty-main-web python -c "
from django.conf import settings
print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
print('DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL)
anymail_settings = getattr(settings, 'ANYMAIL', {})
api_key = anymail_settings.get('SENDGRID_API_KEY', 'НЕ НАСТРОЕН')
if api_key != 'НЕ НАСТРОЕН':
    print('SENDGRID_API_KEY:', api_key[:20] + '...' if len(api_key) > 20 else api_key)
else:
    print('SENDGRID_API_KEY:', api_key)
" 2>nul

echo.
echo 🔍 3. Последние логи email отправки:
docker compose logs realty-main-web --tail 20 | findstr /C:"📧" /C:"✅" /C:"❌" /C:"Email" /C:"SendGrid"

echo.
echo 🧪 4. Быстрый тест отправки:
set /p test_email="Введите email для теста (или Enter для пропуска): "
if not "%test_email%"=="" (
    echo Отправляем тестовый OTP на %test_email%...
    powershell -Command "$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/send-otp/' -Method POST -ContentType 'application/json' -Body '{\"email\": \"%test_email%\"}' -ErrorAction SilentlyContinue; if ($response) { Write-Host 'Ответ сервера:'; $response.Content } else { Write-Host '❌ Ошибка подключения к серверу' }"
)

echo.
echo 📋 ДИАГНОСТИКА:
echo ==============
echo ✅ Если видите "anymail.backends.sendgrid.EmailBackend" - SendGrid настроен
echo ✅ Если видите "✅ Email успешно отправлен" - все работает
echo ❌ Если видите "filebased.EmailBackend" - нужно настроить SendGrid
echo ❌ Если видите ошибки - проверьте настройки в .env
echo.
echo 📚 Подробные инструкции:
echo - SENDGRID_ПОЛНАЯ_ИНСТРУКЦИЯ.md
echo - SENDGRID_ШПАРГАЛКА.md
echo.
pause

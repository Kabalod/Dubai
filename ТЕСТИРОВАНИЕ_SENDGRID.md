# 🧪 Тестирование SendGrid и полного цикла регистрации

## ✅ Статус настройки

**SendGrid успешно настроен и готов к работе!**

- ✅ SendGrid API ключ добавлен в docker-compose.yml
- ✅ django-anymail установлен
- ✅ Email backend настроен правильно
- ✅ Health check показывает: `sendgrid_configured: true`

## 🧪 Как протестировать

### Вариант 1: Автоматический тест (рекомендуется)

```powershell
# Замените на свой реальный email!
.\test-registration.ps1 -Email "ваш-email@gmail.com"
```

### Вариант 2: Ручное тестирование

1. **Регистрация пользователя:**
```powershell
$headers = @{'Content-Type' = 'application/json'}
$body = @{
    email = "ваш-email@gmail.com"
    first_name = "Test"
    last_name = "User"
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body
```

2. **Проверьте почту** - должно прийти письмо от `noreply@kabalod.online` с 6-значным кодом

3. **Подтверждение OTP:**
```powershell
$verifyBody = @{
    email = "ваш-email@gmail.com"
    code = "123456"  # код из письма
    first_name = "Test"
    last_name = "User"
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/verify-otp/' -Method POST -Headers $headers -Body $verifyBody
```

## 🔧 Проверка статуса

```powershell
# Health check
curl http://localhost:8000/api/health/

# Логи бекенда
docker compose logs realty-main-web --tail 10
```

## 📧 Настройки SendGrid

```
✅ API Key: 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
✅ From Email: noreply@kabalod.online  
✅ Backend: anymail.backends.sendgrid.EmailBackend
```

## 🚀 Готово для деплоя

Все настройки готовы для Railway:
- ✅ Локальное тестирование работает
- ✅ SendGrid настроен
- ✅ Переменные окружения готовы для продакшна

Теперь можно коммитить и деплоить на Railway!

---

**⚠️ Важно:** Используйте свой реальный email адрес для тестирования, чтобы убедиться что письма действительно приходят.

# 🧪 Тестирование SendGrid интеграции

## 🚀 Быстрый тест

После получения API ключа и верификации email в SendGrid:

### Вариант 1: Автоматический скрипт
```bash
.\setup-sendgrid.bat "SG.ваш-api-ключ" "ваш-verified-email@domain.com"
```

### Вариант 2: Ручная настройка

1. **Создайте файл `.env`** в корне проекта:
```env
SENDGRID_API_KEY=SG.ваш-sendgrid-api-ключ
DEFAULT_FROM_EMAIL=Dubai Real Estate <ваш-verified-email@domain.com>
```

2. **Перезапустите бекенд:**
```bash
docker compose down realty-main-web
docker compose --profile backend up -d
```

3. **Проверьте логи настройки:**
```bash
docker compose logs realty-main-web --tail 10
```
Вы должны увидеть: `✅ SendGrid настроен. From email: ...`

4. **Отправьте тестовый OTP:**
```bash
Invoke-WebRequest -Uri http://localhost:8000/api/auth/send-otp/ -Method POST -ContentType "application/json" -Body '{"email": "ваш-email@domain.com"}'
```

## 🔍 Диагностика проблем

### Проверка настроек:
```bash
docker compose exec realty-main-web python -c "
from django.conf import settings
print(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
print(f'SENDGRID_API_KEY: {getattr(settings, \"ANYMAIL\", {}).get(\"SENDGRID_API_KEY\", \"НЕ НАСТРОЕН\")[:20]}...')
"
```

### Типичные ошибки:

1. **"The from address does not match a verified Sender Identity"**
   - В SendGrid должен быть верифицирован точно тот email, который в DEFAULT_FROM_EMAIL

2. **"Forbidden"**
   - Проверьте права API ключа (должен иметь Mail Send: Full Access)

3. **"Invalid API key"**
   - Проверьте что ключ начинается с "SG." и скопирован полностью

## ✅ Успешная интеграция

При успешной настройке:
- В логах: `✅ Email успешно отправлен на email@domain.com`
- Письмо приходит на указанную почту в течение 1-2 минут
- OTP код больше не отображается в Debug режиме (безопасность)

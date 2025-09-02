# Настройка отправки OTP на email

## Вариант 1: Gmail SMTP (Рекомендуется для тестирования)

### Шаги настройки:

1. **Включите двухфакторную аутентификацию** в Google аккаунте
2. **Создайте пароль приложения:**
   - Перейдите в настройки Google аккаунта
   - Безопасность → Двухэтапная аутентификация → Пароли приложений
   - Создайте пароль для "Другое приложение"

3. **Установите переменные окружения:**
```bash
# В .env файл или переменные системы
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Dubai Real Estate <your-email@gmail.com>
```

## Вариант 2: SendGrid (Для продакшна)

1. **Зарегистрируйтесь на SendGrid.com**
2. **Получите API ключ**
3. **Установите переменную:**
```bash
SENDGRID_API_KEY=your-sendgrid-api-key
```

## Вариант 3: Временное решение (File backend)

Письма будут сохраняться в файлы для тестирования.

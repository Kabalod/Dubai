# ⚡ Быстрая настройка Gmail SMTP

## 🎯 Решение за 2 минуты

Пока reg.ru настраивается, можно быстро протестировать с Gmail:

### 1. Что нужно:
- ✅ Ваш Gmail аккаунт  
- ✅ App Password (2FA должен быть включен)

### 2. Получить App Password:
1. **Google Account** → https://myaccount.google.com/
2. **Security** → **2-Step Verification** (включить если не включен)
3. **App passwords** → **Select app: Mail** → **Generate**
4. **Скопируйте** 16-значный пароль (например: `abcd efgh ijkl mnop`)

### 3. Обновить docker-compose.yml:
```yaml
# Gmail SMTP (для быстрого тестирования)
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=ваш.email@gmail.com
- EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop  # App Password
- DEFAULT_FROM_EMAIL=ваш.email@gmail.com
```

### 4. Перезапустить и тестировать:
```powershell
docker compose restart realty-main-web
# Письма будут приходить от вашего Gmail!
```

## 💡 Преимущества:
- ✅ **Работает сразу** (99.9% delivery rate)
- ✅ **Не требует** настройки reg.ru  
- ✅ **Быстрое тестирование** полной цепочки
- ✅ **Реальные письма** на любые email адреса

**Готовы попробовать?** Просто дайте ваш Gmail - я обновлю настройки! 📧

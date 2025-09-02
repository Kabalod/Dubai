# 🚀 БЫСТРАЯ НАСТРОЙКА EMAIL ОТПРАВКИ

## ✅ Сейчас работает:
- OTP коды генерируются ✅
- Письма сохраняются в файлы ✅ 
- Можно просматривать содержимое ✅

## 📧 Для реальной отправки на email:

### 1. Создайте файл `.env` в корне проекта:
```bash
# Создайте файл: C:\Users\User\Desktop\Dubai\.env
# И добавьте в него (замените на свои данные):

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Dubai Real Estate <your-email@gmail.com>
```

### 2. Получите пароль приложения Gmail:
1. Войдите в Gmail
2. Настройки Google аккаунта → Безопасность
3. Включите двухэтапную аутентификацию
4. Создайте пароль приложения: https://myaccount.google.com/apppasswords
5. Скопируйте 16-символьный пароль в EMAIL_HOST_PASSWORD

### 3. Перезапустите бекенд:
```bash
docker compose down realty-main-web
docker compose --profile backend up -d
```

## 🔍 Просмотр текущих писем в файлах:
```bash
# Список писем:
docker compose exec realty-main-web ls -la /tmp/emails/

# Читать последнее письмо:
docker compose exec realty-main-web cat /tmp/emails/*.log
```

## ✅ После настройки:
- OTP коды будут приходить на реальный email
- В DEBUG режиме код также показывается в ответе API
- Пользователи смогут получать коды на свою почту

**Сейчас система работает корректно, просто письма сохраняются в файлы вместо отправки!**

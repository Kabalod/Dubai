# 📧 Настройка отправки OTP на email

## 🚀 Быстрая настройка Gmail SMTP

### 1. Подготовка Gmail аккаунта:
1. Войдите в свой Gmail аккаунт
2. Перейдите в [Настройки Google аккаунта](https://myaccount.google.com)
3. Включите **двухфакторную аутентификацию** (если еще не включена)
4. Перейдите в [Пароли приложений](https://myaccount.google.com/apppasswords)
5. Создайте пароль для "Другое приложение" - назовите "Dubai Real Estate"
6. Скопируйте 16-символьный пароль

### 2. Создайте .env файл в корне проекта:
```bash
# Создайте файл .env в папке C:\Users\User\Desktop\Dubai\.env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Dubai Real Estate <your-email@gmail.com>
```

### 3. Перезапустите бекенд:
```bash
docker compose down realty-main-web
docker compose --profile backend up -d
```

## 📁 Альтернатива: Просмотр писем в файлах

Если не хотите настраивать SMTP, письма сохраняются в `/tmp/emails` внутри контейнера.

Посмотреть их можно командой:
```bash
docker compose exec realty-main-web ls -la /tmp/emails/
docker compose exec realty-main-web cat /tmp/emails/*.eml
```

## 🔧 Другие SMTP провайдеры

### Yandex:
```bash
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yandex.ru
EMAIL_HOST_PASSWORD=your-password
```

### Mail.ru:
```bash
EMAIL_HOST=smtp.mail.ru
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@mail.ru
EMAIL_HOST_PASSWORD=your-password
```

### SendGrid (Профессиональный):
```bash
SENDGRID_API_KEY=your-sendgrid-api-key
```

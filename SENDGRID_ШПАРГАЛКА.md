# 📧 SendGrid: Быстрая шпаргалка

## 🚀 Экспресс-настройка (5 минут)

### 1️⃣ Получите SendGrid данные:
- **Сайт**: https://sendgrid.com/ (регистрация бесплатная)
- **Создайте Sender Identity** (Settings → Sender Authentication)
- **Получите API ключ** (Settings → API Keys → Create с правами Mail Send)

### 2️⃣ Автоматическая настройка:
```bash
.\quick-setup-sendgrid.bat "SG.ваш-api-ключ" "ваш-verified-email@gmail.com"
```

### 3️⃣ Проверка:
- ✅ В логах: `✅ Email успешно отправлен`
- ✅ На почте: письмо с OTP кодом

---

## 🔧 Ручная настройка

### Создайте `.env` файл:
```env
SENDGRID_API_KEY=SG.ваш-ключ
DEFAULT_FROM_EMAIL=Dubai Real Estate <ваш-email@domain.com>
```

### Перезапустите:
```bash
docker compose down realty-main-web
docker compose --profile backend up -d
```

---

## 🧪 Тестирование

### Отправка OTP:
```bash
$response = Invoke-WebRequest -Uri http://localhost:8000/api/auth/send-otp/ -Method POST -ContentType "application/json" -Body '{"email": "test@example.com"}'; $response.Content
```

### Проверка настроек:
```bash
docker compose logs realty-main-web --tail 10 | findstr SendGrid
```

---

## ❌ Частые ошибки

| Ошибка | Решение |
|--------|---------|
| "from address does not match" | Email в .env ≠ верифицированному в SendGrid |
| "Forbidden" | Неправильный API ключ или нет прав Mail Send |
| "file backend" | .env не читается, перезапустите контейнер |

---

## ✅ Готово!

После настройки:
- 📧 Реальные OTP коды на почту
- 🌐 Полная регистрация на http://localhost:3000/auth
- 🔐 Google OAuth работает параллельно

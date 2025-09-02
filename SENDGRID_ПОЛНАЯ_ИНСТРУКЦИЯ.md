# 📧 SendGrid: Полная инструкция от А до Я

## 🎯 Цель
Настроить отправку реальных OTP кодов на email через SendGrid для регистрации пользователей.

---

## 📋 ШАГ 1: Создание аккаунта SendGrid

### 1.1 Регистрация
1. Перейдите на https://sendgrid.com/
2. Нажмите **"Start for free"** или **"Sign Up"**
3. Заполните форму регистрации:
   - **Email**: ваш рабочий email (будет использоваться для верификации)
   - **Password**: надежный пароль
   - **Company**: любое название (например: "Dubai Real Estate")
4. Нажмите **"Create Account"**

### 1.2 Подтверждение email
1. Проверьте почту и нажмите на ссылку подтверждения
2. Войдите в панель SendGrid

### 1.3 Заполнение профиля (если требуется)
- SendGrid может запросить дополнительную информацию о компании
- Заполните базовую информацию (можно указать тестовые данные)

---

## 🔑 ШАГ 2: Верификация Sender Identity (КРИТИЧЕСКИ ВАЖНО!)

⚠️ **БЕЗ ЭТОГО ШАГА ПИСЬМА НЕ БУДУТ ОТПРАВЛЯТЬСЯ!**

### 2.1 Переход к настройкам
1. В панели SendGrid слева найдите **"Settings"**
2. Выберите **"Sender Authentication"**

### 2.2 Single Sender Verification
1. Нажмите **"Get Started"** в разделе "Single Sender Verification"
2. Нажмите **"Create New Sender"**

### 2.3 Заполнение формы Sender
```
From Name: Dubai Real Estate
From Email: ваш-email@gmail.com (или любой ваш реальный email)
Reply To: тот же email
Company Name: Dubai Real Estate
Address Line 1: любой адрес
City: любой город
State: любой регион
Zip Code: любой индекс
Country: ваша страна
```

### 2.4 Подтверждение Sender
1. Нажмите **"Create"**
2. Проверьте почту (ваш-email@gmail.com)
3. Нажмите на ссылку подтверждения в письме
4. Вернитесь в SendGrid - статус должен стать **"Verified"** ✅

---

## 🔐 ШАГ 3: Создание API ключа

### 3.1 Переход к API Keys
1. В панели SendGrid: **"Settings"** → **"API Keys"**
2. Нажмите **"Create API Key"**

### 3.2 Настройка API Key
1. **API Key Name**: `Dubai Real Estate OTP`
2. **API Key Permissions**: выберите **"Restricted Access"**
3. В списке разрешений найдите **"Mail Send"**
4. Установите **"Full Access"** для Mail Send
5. Все остальные разрешения оставьте **"No Access"**
6. Нажмите **"Create & View"**

### 3.3 Сохранение ключа
1. **СКОПИРУЙТЕ** ключ полностью (начинается с `SG.`)
2. **СОХРАНИТЕ** в надежном месте - он больше не покажется!

Пример ключа: `SG.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`

---

## ⚙️ ШАГ 4: Настройка проекта

### 4.1 Создание .env файла
Создайте файл `.env` в корне проекта (`C:\Users\User\Desktop\Dubai\.env`):

```env
# SendGrid настройки
SENDGRID_API_KEY=SG.ваш-полный-api-ключ-который-скопировали
DEFAULT_FROM_EMAIL=Dubai Real Estate <ваш-verified-email@gmail.com>
```

⚠️ **ВАЖНО**: 
- Email в `DEFAULT_FROM_EMAIL` должен ТОЧНО совпадать с верифицированным в SendGrid
- Не забудьте угловые скобки: `<email@domain.com>`

### 4.2 Пример заполненного .env:
```env
SENDGRID_API_KEY=SG.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
DEFAULT_FROM_EMAIL=Dubai Real Estate <myemail@gmail.com>
```

---

## 🚀 ШАГ 5: Перезапуск системы

### 5.1 Остановка бекенда
```bash
docker compose down realty-main-web
```

### 5.2 Запуск с новыми настройками
```bash
docker compose --profile backend up -d
```

### 5.3 Проверка логов
```bash
docker compose logs realty-main-web --tail 10
```

**Вы должны увидеть:**
```
📧 Настройка SendGrid email backend с ключом: SG.abc123...
✅ SendGrid настроен. From email: Dubai Real Estate <myemail@gmail.com>
```

---

## 🧪 ШАГ 6: Тестирование

### 6.1 Отправка тестового OTP
```bash
$response = Invoke-WebRequest -Uri http://localhost:8000/api/auth/send-otp/ -Method POST -ContentType "application/json" -Body '{"email": "ваш-email@gmail.com"}'; $response.Content
```

### 6.2 Что должно произойти:
1. **В логах бекенда:**
   ```
   📧 Отправляем email на ваш-email@gmail.com с OTP: 123456
   📧 From email: Dubai Real Estate <ваш-email@gmail.com>
   📧 Email backend: anymail.backends.sendgrid.EmailBackend
   ✅ Email успешно отправлен на ваш-email@gmail.com
   ```

2. **В ответе API:**
   ```json
   {
     "message": "OTP code sent successfully",
     "email": "ваш-email@gmail.com",
     "email_sent": true,
     "expires_in": 600
   }
   ```

3. **На почте** (в течение 1-2 минут):
   ```
   Subject: Dubai Real Estate - Verification Code
   
   Hello!
   
   Your verification code for Dubai Real Estate Platform is: 123456
   
   This code will expire in 10 minutes.
   ```

---

## 🌐 ШАГ 7: Тестирование полной регистрации

### 7.1 Откройте фронтенд
```bash
# Если не запущен:
npm run dev
```
Перейдите на http://localhost:3000/auth

### 7.2 Процесс регистрации:
1. Выберите "Sign Up"
2. Введите ваш email
3. Нажмите "SIGN UP"
4. **Проверьте почту** - должен прийти OTP код
5. Введите полученный код
6. Заполните профиль
7. Готово! ✅

---

## 🔧 ДИАГНОСТИКА ПРОБЛЕМ

### ❌ Проблема: "The from address does not match a verified Sender Identity"
**Решение:**
- Проверьте что email в `.env` точно совпадает с верифицированным в SendGrid
- Убедитесь что Sender Identity имеет статус "Verified" ✅

### ❌ Проблема: "Forbidden" / "Unauthorized"
**Решение:**
- Проверьте что API ключ скопирован полностью
- Убедитесь что API ключ имеет права "Mail Send: Full Access"

### ❌ Проблема: "Still using file backend"
**Решение:**
- Проверьте что `.env` файл создан в правильном месте
- Перезапустите контейнер: `docker compose down realty-main-web && docker compose --profile backend up -d`

### 🔍 Проверка настроек:
```bash
docker compose exec realty-main-web python -c "
from django.conf import settings
print(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
print(f'SENDGRID_API_KEY: {getattr(settings, \"ANYMAIL\", {}).get(\"SENDGRID_API_KEY\", \"НЕ НАСТРОЕН\")[:20]}...')
"
```

---

## ✅ ГОТОВО!

После выполнения всех шагов:
- ✅ OTP коды будут приходить на реальную почту
- ✅ Пользователи смогут регистрироваться через email
- ✅ Google OAuth тоже работает
- ✅ Система готова к продакшну

**Теперь ваша система регистрации полностью функциональна!** 🎉

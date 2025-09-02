# 📧 Создание почтового ящика в reg.ru

## 🚨 ПРОБЛЕМА
```
❌ Ошибка: (535, b'Incorrect authentication data')
```

**Причина:** Почтовый ящик `noreply@kabalod.online` не создан в панели управления reg.ru

## 🔧 РЕШЕНИЕ

### 1. Зайдите в панель управления хостингом:
**URL:** https://sm12.hosting.reg.ru:1500/  
**Логин:** u3237525  
**Пароль:** um3YeEn1AcDN12JX  

### 2. Создайте почтовый ящик:
1. Найдите раздел **"Почта"** или **"Email"**
2. Нажмите **"Создать почтовый ящик"**
3. Заполните:
   - **Email:** `noreply@kabalod.online`
   - **Пароль:** `NoreplyPass123!` (запомните его!)
4. Нажмите **"Создать"**

### 3. Обновите настройки в docker-compose.yml:
```yaml
- EMAIL_HOST_USER=noreply@kabalod.online
- EMAIL_HOST_PASSWORD=NoreplyPass123!  # новый пароль
```

### 4. Или используйте существующий ящик:
Если у вас уже есть почтовый ящик на домене kabalod.online:
```yaml
- EMAIL_HOST_USER=admin@kabalod.online  # ваш существующий ящик
- EMAIL_HOST_PASSWORD=ваш_пароль_от_ящика
- DEFAULT_FROM_EMAIL=admin@kabalod.online
```

## 🎯 Альтернативное решение - Gmail SMTP

Если reg.ru сложно настроить, можно быстро использовать Gmail:

```yaml
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=ваш.gmail@gmail.com
- EMAIL_HOST_PASSWORD=app_password  # App Password от Google
- DEFAULT_FROM_EMAIL=ваш.gmail@gmail.com
```

**Как получить App Password:**
1. Google Account → Security → 2-Step Verification (включить)
2. App passwords → Mail → Generate
3. Используйте сгенерированный пароль

## 📞 БЫСТРЫЙ СПОСОБ

**Скажите какой вариант предпочитаете:**
1. 🔧 Создать ящик noreply@kabalod.online в reg.ru
2. 📧 Использовать ваш Gmail для тестирования  
3. 📋 Использовать другой существующий ящик на kabalod.online

Любой вариант займет 2-3 минуты!

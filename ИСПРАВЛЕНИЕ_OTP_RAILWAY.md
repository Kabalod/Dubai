# 🔧 Исправление OTP на Railway

## ❌ Проблема
OTP код приходит на почту, но не проходит верификацию - "Invalid OTP code. Please try again."

## 🔍 Причина
На Railway не были настроены настройки кэша! Django использовал кэш по умолчанию, который не работает между запросами.

## ✅ Исправления

### 1. Добавлены настройки кэша в `settings_railway.py`:
```python
# Cache настройки - Redis для Railway, локальный для разработки
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback к локальному кэшу
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
```

### 2. Добавлен `django-redis` в `requirements.txt`:
```
django-redis>=5.4.0
```

### 3. Добавлена отладочная информация в `auth_views_simple.py`:
- Логи сохранения OTP в кэш
- Логи поиска OTP в кэше
- Детальная диагностика

## 🚀 Как задеплоить

1. **Закоммить изменения**:
   ```bash
   git add .
   git commit -m "Fix OTP cache: Add Redis settings for Railway"
   git push
   ```

2. **Railway автоматически пересоберет** с новыми настройками

3. **Проверить деплой**:
   - Зарегистрироваться через фронт
   - Проверить что OTP приходит на почту
   - Ввести OTP код - должен пройти верификацию

## 🔍 Отладка

Если все еще не работает, проверь логи Railway:
1. Зайди в Railway Dashboard
2. Выбери бекенд сервис
3. Посмотри логи в разделе "Deployments"
4. Ищи строки с 🔍, 💾, ❌ для диагностики кэша

## 📧 Email настройки

Email уже настроен и работает:
- SendGrid API (основной)
- reg.ru SMTP (fallback)
- Реальные письма отправляются

## 🎯 Ожидаемый результат

После деплоя:
- ✅ OTP код приходит на почту
- ✅ OTP код проходит верификацию
- ✅ Пользователь создается в базе данных
- ✅ JWT токены генерируются
- ✅ Полная регистрация работает

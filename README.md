# 🏗️ Dubai MVP - Real Estate Analytics Platform

> **MVP Status**: ✅ **Production Ready** | 🚀 **Deployed on Railway** | 🔐 **OTP Authentication Active**

Централизованная система для анализа рынка недвижимости Дубая с современной OTP аутентификацией.

## 🎯 Что это?

**Dubai MVP** - это полнофункциональная платформа для анализа недвижимости с:
- 🔐 **OTP аутентификация** через email (SendGrid)
- 🏠 **API для недвижимости** (готов к расширению)
- 📊 **Аналитические дашборды** (базовая версия)
- 🤖 **Автоматизированный деплой** и мониторинг

## 🚀 Быстрый старт

### 🌐 Продакшен (Railway)
Система уже развёрнута и готова к использованию:

- **Frontend**: https://frontend-production-5c48.up.railway.app/
- **Backend API**: https://workerproject-production.up.railway.app/api/health/
- **OTP Test**: https://frontend-production-5c48.up.railway.app/auth

### 💻 Локальная разработка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Kabalod/Workerproject.git
cd Workerproject

# 2. Запустить автоматизированный менеджер
.\manage-project.ps1 dev

# 3. Или через Docker Compose
docker-compose -f docker-compose.dev.yml up --build
```

## 🏗️ Архитектура

```
Dubai MVP
├── 🎨 Frontend (React + Vite + Ant Design)
│   ├── OTP Authentication UI
│   ├── Property Search Interface  
│   └── Analytics Dashboard
├── 🔧 Backend (Django + DRF + PostgreSQL)
│   ├── OTP API (/api/auth/send-otp/, /api/auth/verify-otp/)
│   ├── User Management (/api/auth/register/, /api/auth/login/)
│   └── Health Check (/api/health/)
├── 📧 Email Service (SendGrid)
├── 🗄️ Database (PostgreSQL on Railway)
└── 🚀 Deployment (Railway + GitHub Actions)
```

## 🔐 OTP Authentication Flow

1. **Регистрация**: Пользователь вводит email → получает 6-значный код
2. **Верификация**: Вводит код → система создаёт аккаунт + JWT токены
3. **Авторизация**: Токены сохраняются в localStorage для последующих запросов

### 📧 Настройка SendGrid

```bash
# В Railway UI добавьте переменные:
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=your_verified_email@domain.com
```

## 🛠️ Автоматизированное управление

Используйте главный менеджер проекта:

```powershell
# Проверка статуса системы
.\manage-project.ps1 status

# Автоматическое исправление проблем
.\manage-project.ps1 fix

# Полный деплой в продакшен
.\manage-project.ps1 prod

# Мониторинг в реальном времени
.\manage-project.ps1 watch

# Локальная разработка
.\manage-project.ps1 dev
```

## 📊 API Endpoints

### 🔐 Authentication
- `POST /api/auth/send-otp/` - Отправка OTP кода
- `POST /api/auth/verify-otp/` - Верификация OTP кода
- `POST /api/auth/register/` - Регистрация пользователя
- `POST /api/auth/login/` - Вход в систему

### 🏠 Properties (MVP Placeholders)
- `GET /api/properties/` - Список объектов недвижимости
- `GET /api/areas/` - Районы Дубая
- `GET /api/buildings/` - Здания и комплексы

### 📈 Analytics
- `GET /api/analytics/` - Базовая аналитика системы
- `GET /api/health/` - Статус системы

## 🐳 Docker Configuration

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .

# Оптимизированная установка зависимостей
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        psycopg[binary] \
        django==4.2.* \
        djangorestframework \
        django-cors-headers \
        djangorestframework-simplejwt \
        django-anymail \
        environs \
        dj-database-url

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --run-syncdb && python manage.py runserver 0.0.0.0:8000"]
```

### Frontend Dockerfile
```dockerfile
# Multi-stage build для оптимизации
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json yarn.lock ./
RUN corepack enable && yarn install
COPY . .
RUN yarn build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔧 Переменные окружения

### Backend (Railway)
```env
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
DEBUG=false
DJANGO_ALLOWED_HOSTS=workerproject-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://frontend-production-5c48.up.railway.app
SENDGRID_API_KEY=your-sendgrid-key
DEFAULT_FROM_EMAIL=your-email@domain.com
SECURE_SSL_REDIRECT=true
```

### Frontend (Railway)
```env
VITE_API_BASE_URL=https://workerproject-production.up.railway.app
```

## 🧪 Тестирование

### Автоматические тесты
```bash
# Запуск комплексной проверки
.\scripts\comprehensive-check.ps1

# Проверка Railway статуса
.\scripts\railway-health-check.ps1

# Мониторинг логов
.\scripts\railway-monitor.ps1
```

### Ручное тестирование OTP
1. Откройте https://frontend-production-5c48.up.railway.app/auth
2. Введите email: `kbalodk@gmail.com`
3. Нажмите **SIGN UP**
4. Проверьте почту на код от SendGrid
5. Введите 6-значный код
6. Завершите регистрацию

## 📈 Мониторинг и логи

### Railway Dashboard
- **Backend**: https://railway.app/project/ccd447ca-39b8-444a-b8d1-28ac1ec894a8
- **Логи**: `npx @railway/cli@latest logs`
- **Статус**: `npx @railway/cli@latest status`

### Health Checks
- **Backend**: https://workerproject-production.up.railway.app/api/health/
- **Frontend**: https://frontend-production-5c48.up.railway.app/
- **Database**: Автоматически через Django ORM

## 🚀 CI/CD Pipeline

### GitHub Actions
Автоматический деплой при push в `prod` ветку:
1. **Комплексная проверка** кода
2. **Валидация** Dockerfile и настроек
3. **Деплой** в Railway
4. **Health check** и интеграционные тесты

### Ручной деплой
```bash
git add -A
git commit -m "feat: your changes"
git push origin prod
```

## 🔍 Troubleshooting

### Частые проблемы
1. **502 Backend Error**: Проверьте логи Railway и переменные окружения
2. **CORS ошибки**: Убедитесь что `CORS_ALLOWED_ORIGINS` содержит правильный домен
3. **Email не приходит**: Проверьте `SENDGRID_API_KEY` и `DEFAULT_FROM_EMAIL`
4. **Database ошибки**: Проверьте `DATABASE_URL` в Railway

### Диагностические команды
```bash
# Проверка всей системы
.\manage-project.ps1 status

# Автоматическое исправление
.\manage-project.ps1 fix

# Детальная диагностика
.\scripts\comprehensive-check.ps1
```

## 📚 Документация

- **[Структура проекта](./docs/PROJECT_STRUCTURE.md)**
- **[API документация](./docs/api/overview.md)**
- **[Руководство по деплою](./docs/deployment/quick-start.md)**
- **[Troubleshooting](./docs/troubleshooting/common-issues.md)**

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature ветку: `git checkout -b feature/amazing-feature`
3. Commit изменения: `git commit -m 'Add amazing feature'`
4. Push в ветку: `git push origin feature/amazing-feature`
5. Создайте Pull Request

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/Kabalod/Workerproject/issues)
- **Email**: kbalodk@gmail.com
- **Telegram**: @kabalod

---

**🎉 Dubai MVP готов к продакшену!** Система полностью автоматизирована и готова к масштабированию.

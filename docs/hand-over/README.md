### Передача проекта (Handover)

Этот документ описывает, как запустить, проверить и сопровождать продуктовую версию.

#### 1) Архитектура (высокоуровнево)
- Frontend: `apps/DXB-frontend-develop` (Vite/React). Prod-сборка раздаётся через Nginx.
- Backend: `apps/realty-main` (Django REST, SimpleJWT). БД — Postgres.
- CI/CD: GitHub Actions (CI для FE/BE, e2e, CodeQL), Dependabot.
- Мониторинг/логи: базовые конфиги в `monitoring/`, `configs/`.

#### 2) Переменные окружения
См. `env.example`. Минимально для прод:
- `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `MOCK_WEBHOOK_SECRET`
- (опционально) `GOOGLE_CLIENT_ID/SECRET`, `FRONTEND_URL`, `REDIS_URL`

#### 3) Развёртывание (prod)
- Бэкенд: применить миграции (`0001`, `0002_payment_event_audit`), запустить приложение (gunicorn/uvicorn) за reverse-proxy (Nginx).
- Фронтенд: `npm ci && npm run build` → раздача `dist/`.
- Вебхуки: открыть `POST /api/billing/webhook/{provider}/` и настроить секрет.

#### 4) Роли и доступы
- Роли: `free`, `paid`, `admin` (см. `UserProfile`).
- Доступы: `/analytics` — только paid; `/admin/*` и `/api/reports/` — только admin.

#### 5) Контракты API
- Общее: `docs/api/contracts.md`
- Вебхуки: `docs/api/billing-webhooks.md`

#### 6) Проверки качества
- CI: линтеры/типы, pytest, e2e (Playwright). См. `.github/workflows/`.
- Smoke-прогон: `docs/hand-over/SMOKE.md`.

#### 7) Релизы
- Мердж PR → запуск CI → tag релиза (по желанию) → выкладка.
- Релизные заметки: собрать из PR (What/Why/How to test).

#### 8) Поддержка
- Issues для багов/запросов изменений.
- Dependabot PR — еженедельно (npm/pip/docker/actions).

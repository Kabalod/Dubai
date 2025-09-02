### Production Guide

Чеклист перед релизом:
- CI: фронтенд/бэкенд CI зелёные; e2e workflow зелёный.
- CodeQL/Dependabot подключены; критичные алерты закрыты.
- Миграции применены (`0001`, `0002_payment_event_audit`).
- Секреты заданы: `SECRET_KEY`, БД, `MOCK_WEBHOOK_SECRET`, OAuth (по необходимости).
- Nginx: security headers, gzip/brotli, HTTP→HTTPS редирект.
- Мониторинг/логи: базовые дашборды и алерты активны.

Деплой:
- Backend: контейнер Django + Postgres + Redis (при наличии), применить миграции.
- Frontend: build Vite, раздача через Nginx/статический хостинг.
- Webhook: открыть маршрут `/api/billing/webhook/{provider}/` и секрет.

Security headers (Nginx):
- `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`, `Permissions-Policy`.

Rollback:
- Бэкапы БД, версия образов, быстрый откат compose/helm.

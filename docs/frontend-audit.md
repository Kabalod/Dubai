# Frontend Audit (Dubai MVP)

## Чекпоинт 1: API base URL и proxy

Что было:
- `src/config.ts` хардкодил прод URL Railway и игнорировал Vite env
- `vite.config.ts` подставлял `/api` дефолтом
- `apps/DXB-frontend-develop/nginx.conf` проксировал на конкретный домен Railway

Что сделано:
- `src/config.ts`: теперь API_BASE_URL берётся из `VITE_FRONTEND_API_URL` (или пустая строка → относительный путь)
- `vite.config.ts`: дефолт API убран, значение берётся из env
- `nginx.conf`: прокси настроен на относительный `/api/` (или внутренний сервис `backend:8000`), без хардкода домена

Как задавать API URL:
- Dev: создайте `apps/DXB-frontend-develop/.env` с `VITE_FRONTEND_API_URL=http://localhost:8000`
- Prod: используйте платформенные переменные окружения сборки (Vite) или общий прокси, отдающий фронт и бэк с одного домена

Дальше:
- Удалить дублирующий API-клиент и выровнять все вызовы на один модуль
- Синхронизировать эндпоинты оплаты с бекендом (или выключить раздел оплаты)


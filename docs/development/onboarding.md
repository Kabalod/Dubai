### Onboarding

- Требования: Node >=22, Python >=3.12, Docker (опционально), PostgreSQL.
- Порты: см. `PORTS_README.md`.

Локальный запуск:
- Backend: `docker compose -f docker-compose.ci.yml up -d` → `cd apps/realty-main` → `pip install -r requirements.txt` → `python manage.py migrate` → `python manage.py runserver 8000`.
- Frontend: `cd apps/DXB-frontend-develop` → `npm ci` → `npm run dev` (порт 3000).

Тесты:
- Backend: `pytest -q` (нужны переменные из `.env` при необходимости).
- E2E: `cd e2e && npm ci && npm test` (env: `FRONTEND_URL`, `API_URL`).

Документация:
- Контракты API: `docs/api/contracts.md`
- Webhooks: `docs/api/billing-webhooks.md`
- E2E: `docs/qa/e2e.md`

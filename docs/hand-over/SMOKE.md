### Smoke-тесты (15 минут)

1) Аутентификация
- POST `/api/auth/register/` → 200/201, получить токены.
- GET `/api/auth/profile/` с Bearer → 200.

2) Подписка
- GET `/api/billing/subscription/` (auth) → 200 (free|active).
- POST `/api/billing/mock-pay/` (auth) → 200; GET `/api/analytics/` → 200 (paid).

3) Доступы
- Как free: GET `/api/analytics/` → 403/401; GET `/api/reports/` → 403.
- Как admin: GET `/api/reports/` → 200; фильтры работают.

4) Вебхуки
- POST `/api/billing/webhook/mock/` c корректной подписью → 200 ok/idempotent.
- Неверная подпись → 400.

5) UI (быстро)
- Меню: Main/Analytics/Reports/Account/Profile.
- /admin (только admin): Users/Subscriptions/Payments/Plans — таблицы открываются.

Логи/метрики: ошибки 5xx отсутствуют, ответы < 1с на базовых маршрутах.

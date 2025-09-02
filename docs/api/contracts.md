## Auth

GET `/api/auth/profile`

Response

```json
{ "id": 1, "email": "user@example.com", "role": "free" }
```

## Billing

GET `/api/billing/subscription`

Response

```json
{ "status": "active", "plan": "Paid 30 days", "price_aed": "99.00", "valid_until": "2025-12-31T00:00:00Z", "payment_method": "mock", "last_payment_at": "2025-08-23T10:00:00Z" }
```

POST `/api/billing/mock-pay`

Request

```json
{ "plan": "paid-30", "method": "mock" }
```

Response

```json
{ "message": "Payment succeeded", "plan": "Paid 30 days", "valid_until": "2025-12-31T00:00:00Z" }
```

### Webhooks (провайдерный слой)

POST `/api/billing/webhook/{provider}/`

- Для mock: `{provider} = mock`
- Заголовки:
  - `X-Mock-Signature` или `X-Provider-Signature`: hex(HMAC_SHA256(secret, raw_body)) — обязателен
  - `X-Mock-Event-Id`: уникальный ID события (рекомендуется)
  - `X-Idempotency-Key`: опционально
- Тело (пример):

```json
{
  "type": "payment.succeeded",
  "id": "evt_123",
  "data": {
    "payment_external_id": "pay_456",
    "amount": 99.0,
    "currency": "AED"
  }
}
```

- Ответы:
  - 200 `{ "status": "ok", "event_id": "..." }`
  - 200 `{ "status": "ok", "idempotent": true, "event_id": "..." }`
  - 400 `{ "error": "invalid signature" }`
  - 422 `{ "error": "invalid payload" }`
  - 500 `{ "error": "processing failed" }`

- События → статусы `Payment.status`:
  - `payment.pending` → `pending`
  - `payment.succeeded` → `succeeded` (активация `UserSubscription`)
  - `payment.failed` → `failed`

- Переменные окружения: `MOCK_WEBHOOK_SECRET` — секрет HMAC mock-провайдера.

Аудит: каждая доставка фиксируется в `api_payment_event_audit` c уникальностью `(provider, event_id)`,
что обеспечивает идемпотентность и безопасные ретраи.

## Reports

Доступ: только для роли admin (IsAdminUserStrict).

GET `/api/reports?limit=20&offset=0&user_id=&status=&created_from=&created_to=`

Response

```json
{
  "count": 0,
  "limit": 20,
  "offset": 0,
  "results": [
    { "id": 10, "title": "My Report", "status": "ready", "created_at": "2025-08-23T10:00:00Z", "updated_at": "2025-08-23T10:05:00Z" }
  ]
}
```
### API контракты (MVP)

Базовый префикс: `/api/`

#### Аутентификация
- POST `/auth/register/`
  - Body: `{ "email": string, "username": string, "password": string, "first_name?": string, "last_name?": string }`
  - 200/201: `{ message, user: { id, username, email, first_name, last_name, role }, tokens: { access, refresh } }`

- POST `/auth/login/`
  - Body: `{ "username": string, "password": string }`
  - 200: `{ message, user: {...}, tokens: { access, refresh } }`

- POST `/auth/logout/`
  - Body: `{ "refresh_token"?: string }` — если передан, добавляется в blacklist
  - 200: `{ message }`

- POST `/auth/refresh/`
  - Body: `{ "refresh": string }`
  - 200: `{ access: string }` (ответ SimpleJWT)

#### Профиль
- GET `/auth/profile/` (требуется `Authorization: Bearer <access>`)
  - 200: `{ id, username, email, first_name, last_name, role }`
  - Примечание: необходимо включить маршрут в `apps/realty-main/realty/api/urls.py` (см. `views.profile_me`).

#### Billing
- GET `/billing/subscription/` (auth)
  - 200: `{ status: 'free'|'active'|'expired', plan: string|null, price_aed: string|null, valid_until?: string|null, payment_method?: string|null, last_payment_at?: string|null }`

- POST `/billing/mock-pay/` (auth)
  - Body: `{ plan?: string = 'paid-30', method?: string = 'mock' }`
  - 200: `{ message, plan, valid_until }`

#### Недвижимость (MVP заглушки)
- GET `/properties/`
  - Query: `search, property_type, listing_type, min_price, max_price, bedrooms, area, limit, offset`
  - 200: `{ message?: string, count: number, results: []|Property[] }`

- GET `/areas/`
  - 200: `{ message?: string, count: number, results: []|Area[] }`

- GET `/buildings/`
  - 200: `{ message?: string, count: number, results: []|Building[] }`

#### Analytics
- GET `/analytics/` (role: paid)
  - 200: `{ total_users, total_otp_codes, active_otp_codes, message }` (MVP)

#### Reports
- GET `/reports/` (role: admin)
  - Query: `area?, bedrooms?, limit?, offset?`
  - 200: `{ message?: string, count: number, results: [] }`

#### Коды ошибок (общие)
- 400: `{ error }`
- 401: `{ error }`
- 403: `{ detail }`
- 500: `{ error }`

Совместимость с фронтендом подтверждена, кроме необходимости включить `/auth/profile/`.

### Billing Webhooks — события, подписи, ответы

Путь: `POST /api/billing/webhook/<provider>/`

Заголовки:
- `Content-Type: application/json`
- `X-Provider-Signature: <hmac-sha256>` (принимается также `X-Mock-Signature`)
- `Idempotency-Key?: <string>`

Payload:
```json
{ "id": "evt_123", "type": "payment.succeeded", "data": { "payment_id": "pay_001", "amount": 99, "currency": "AED" } }
```

Ответы:
- `200 { "ok": true, "idempotent?": true }`
- `400 { "error": "bad signature" }`
- `409 { "error": "duplicate" }`
- `422 { "error": "invalid payload" }`

Подпись:
- `signature = hex(hmac_sha256(MOCK_WEBHOOK_SECRET, raw_body))`

События:
- `payment.pending`
- `payment.succeeded`
- `payment.failed`

Замечания:
- Идемпотентность по `event_id`/`Idempotency-Key`
- Логирование аудита: `PaymentEventAudit`

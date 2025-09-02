### Чеклист готовности к передаче

- [ ] CI зелёный: frontend-ci, backend-ci, e2e, CodeQL
- [ ] Применены миграции (`0001`, `0002_payment_event_audit`)
- [ ] Секреты заданы: `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `MOCK_WEBHOOK_SECRET`
- [ ] Доступы: admin/payed протестированы (analytics/reports)
- [ ] Webhook: тест подписи/идемпотентности пройден
- [ ] Документация актуальна: `docs/api/contracts.md`, `docs/api/billing-webhooks.md`
- [ ] Onboarding и prod‑гайд: `docs/development/onboarding.md`, `docs/production/README.md`
- [ ] Storybook сборка открывается, компоненты документированы
- [ ] Бэкапы/rollback‑план описан

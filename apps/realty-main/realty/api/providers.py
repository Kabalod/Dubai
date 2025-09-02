from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Tuple
import hmac
import hashlib
import json


@dataclass
class ProviderConfig:
    name: str
    secret: str


class PaymentProvider(Protocol):
    """Интерфейс платёжного провайдера для вебхуков.

    Задачи:
    - Верифицировать подпись запроса
    - Спарсить полезную нагрузку и нормализовать событие
    - Вернуть кортеж (event_type, event_id, normalized_payload)
    """

    def verify_signature(self, raw_body: bytes, headers: Dict[str, str]) -> bool: ...

    def parse_event(self, raw_body: bytes, headers: Dict[str, str]) -> Tuple[str, str, Dict[str, Any]]: ...


class MockProvider:
    """Mock провайдер для переходного периода.

    Схема подписи: X-Mock-Signature = hex(hmac_sha256(secret, body))
    Идентификатор события: X-Mock-Event-Id (если нет — берём из payload['id']).
    Тип события: payload['type'] ('payment.pending'|'payment.succeeded'|'payment.failed').
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    def _compute_signature(self, raw_body: bytes) -> str:
        mac = hmac.new(self.config.secret.encode('utf-8'), raw_body, hashlib.sha256)
        return mac.hexdigest()

    def verify_signature(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        sent = (
            headers.get('x-mock-signature')
            or headers.get('X-Mock-Signature')
            or headers.get('x-provider-signature')
            or headers.get('X-Provider-Signature')
        )
        if not sent:
            return False
        expected = self._compute_signature(raw_body)
        try:
            return hmac.compare_digest(sent, expected)
        except Exception:
            return False

    def parse_event(self, raw_body: bytes, headers: Dict[str, str]):
        payload = json.loads(raw_body.decode('utf-8') or '{}')
        event_type = payload.get('type') or 'unknown'
        event_id = headers.get('x-mock-event-id') or headers.get('X-Mock-Event-Id') or payload.get('id') or 'unknown'
        normalized = {
            'type': event_type,
            'id': event_id,
            'data': payload.get('data') or payload,
        }
        return event_type, event_id, normalized


def get_provider(name: str, secret: Optional[str]) -> PaymentProvider:
    cfg = ProviderConfig(name=name, secret=secret or '')
    # Пока доступен только Mock
    return MockProvider(cfg)



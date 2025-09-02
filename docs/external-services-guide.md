# Руководство по интеграции с внешними сервисами

## Обзор

Это руководство описывает лучшие практики и предоставляет примеры для интеграции с внешними API и сервисами в рамках платформы Dubai. Мы рассмотрим вопросы аутентификации, обработки ошибок, логирования и асинхронного взаимодействия.

## 1. Архитектура взаимодействия

При работе с внешними сервисами (например, API для получения данных о недвижимости, платежные шлюзы, AI-сервисы) рекомендуется использовать следующий подход:

```
[ Наш Сервис ] -- (HTTP/S Request) --> [ API Gateway ] --> [ Внешний Сервис ]
      |                                      ^
      |                                      |
      +-------- (Кеширование, Логирование) ---+
```

- **API Gateway (Nginx/etc.):** Может использоваться для первичной обработки запросов, SSL-терминации и базового лимитирования.
- **Наш Сервис (Python/FastAPI/Django):** Содержит основную бизнес-логику.
- **Кеширование (Redis):** Обязательно для снижения нагрузки на внешние API и ускорения ответов.

## 2. Шаблон сервисного клиента (Python)

Рекомендуется инкапсулировать всю логику взаимодействия с внешним API в отдельный класс-клиент.

### Пример базового клиента

```python
import requests
import logging
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Настройка логирования
logger = logging.getLogger(__name__)

class BaseApiClient:
    """Базовый класс для взаимодействия с внешними API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        
        # Настройка сессии с retries для отказоустойчивости
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.request(method, url, params=params, json=data, timeout=self.timeout)
            response.raise_for_status()  # Вызовет исключение для 4xx/5xx ответов
            
            logger.info(f"Успешный запрос к {url}: status_code={response.status_code}")
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при запросе к {url}: {e.response.status_code} {e.response.text}")
            # Здесь можно добавить специфическую обработку кодов (401, 403, 429)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка соединения при запросе к {url}: {e}")
            return None

    def get_data(self, resource: str, resource_id: Optional[str] = None, filters: Optional[Dict] = None) -> Optional[Dict]:
        """Получение данных из ресурса."""
        endpoint = f"{resource}/{resource_id}" if resource_id else resource
        return self._request("GET", endpoint, params=filters)

    def post_data(self, resource: str, payload: Dict) -> Optional[Dict]:
        """Отправка данных в ресурс."""
        return self._request("POST", resource, data=payload)

```

### Использование клиента

```python
# Пример использования для гипотетического API данных о недвижимости
REAL_ESTATE_API_URL = "https://api.external-real-estate.com/v1"
API_KEY = "your_secret_api_key"

# Инициализация клиента
property_client = BaseApiClient(base_url=REAL_ESTATE_API_URL, api_key=API_KEY)

# Получение списка объектов
properties = property_client.get_data("properties", filters={"city": "Dubai", "min_price": 500000})
if properties:
    print(f"Найдено {len(properties)} объектов.")

# Создание нового объекта
new_property_payload = {
    "title": "Новая вилла",
    "price": 1200000,
    "location": "Palm Jumeirah"
}
created_property = property_client.post_data("properties", payload=new_property_payload)
if created_property:
    print(f"Создан новый объект с ID: {created_property['id']}")
```

## 3. Асинхронное взаимодействие (с `httpx`)

Для высоконагруженных систем, которые делают много запросов к внешним сервисам, рекомендуется использовать асинхронный клиент.

### Пример асинхронного клиента

```python
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

class AsyncApiClient:
    """Асинхронный клиент для взаимодействия с внешними API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        # Настройка retries для отказоустойчивости
        transport = httpx.AsyncHTTPTransport(retries=3)
        self.client = httpx.AsyncClient(base_url=base_url, headers=headers, transport=transport, timeout=timeout)

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.request(method, endpoint, params=params, json=data)
            response.raise_for_status()
            
            logger.info(f"Успешный асинхронный запрос к {response.url}: status_code={response.status_code}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при асинхронном запросе к {e.request.url}: {e.response.status_code} {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения при асинхронном запросе к {e.request.url}: {e}")
            return None
            
    async def close(self):
        await self.client.aclose()

# ... (методы get_data, post_data аналогичны, но асинхронны)
```

## 4. Лучшие практики

- **Аутентификация:**
  - **Никогда не храните ключи в коде.** Используйте переменные окружения (`.env`) и загружайте их через `os.getenv()` или Pydantic `BaseSettings`.
  - Для OAuth2 используйте библиотеки, такие как `requests-oauthlib`.

- **Обработка ошибок:**
  - **Всегда** оборачивайте запросы в `try...except`.
  - Реализуйте **механизм повторных запросов (retry)** с экспоненциальной задержкой (`backoff`) для временных ошибок (5xx, 429).
  - Четко логируйте ошибки, включая URL, статус-код и тело ответа.

- **Логирование:**
  - Логируйте **каждый** запрос к внешнему API.
  - Включайте в лог `correlation_id`, чтобы можно было отследить всю цепочку вызовов.
  - **Не логируйте** чувствительные данные (API-ключи, пароли, персональные данные).

- **Кеширование:**
  - Используйте Redis для кеширования ответов от `GET` запросов, которые не требуют данных в реальном времени.
  - Устанавливайте адекватное время жизни (TTL) для кеша.

- **Тестирование:**
  - **Используйте `mock`** для изоляции ваших тестов от реальных внешних сервисов. Библиотеки `pytest-mock` и `unittest.mock` отлично подходят для этого.
  - Пишите тесты для всех возможных ответов API: успешных, с ошибками (4xx, 5xx) и таймаутами.

## 5. Обновление документации

Не забудьте добавить этот новый документ в навигацию `docs/mkdocs.yml`, чтобы он появился на вашем сайте документации.

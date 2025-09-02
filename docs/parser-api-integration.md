# Проверка парсера, экспорт в shared-data и интеграция с основным бэкендом

Документ описывает, как подтвердить «здоровье» `parser-service`, выполнить пробный сбор данных и экспорт в `shared-data/`, а затем импортировать эти данные в основной бэкенд (`api-service`).

## Компоненты и порты
- Parser (Django) — контейнер `parser-service`
  - Порт: хост `8002` → контейнер `8000`
  - Маунт: `./shared-data:/shared-data`
- API (Django) — контейнер `api-service`
  - Порт: хост `8000` → контейнер `8000`
  - Маунт: `./shared-data:/shared-data`

## 1) Проверка здоровья парсера

Команда (Windows PowerShell — важно использовать `curl.exe` вместо алиаса):

```bash
curl.exe -s -i http://localhost:8002/health/
```

Ожидаемый ответ: `HTTP/1.1 200 OK` и JSON со статусом `healthy`.

## 2) Пробный парсинг и импорт в БД парсера

Выполнить внутри контейнера парсера:

```bash
docker compose -f docker-compose.prod.yml exec parser-service \
  python parsing/a_buy.py --start-page 1 --end-page 1 --threads 4 --output-dir scraped_data

docker compose -f docker-compose.prod.yml exec parser-service \
  python manage.py import_properties scraped_data --update
```

Примечания:
- `a_buy.py` (и альтернативно `a.py`) сохраняют сырые JSONы и итоговый `properties.json` в `scraped_data/scrape_YYYYMMDD_HHMMSS/`.
- Импорт использует пофайловую обработку из `json_data/*.json`. Если в агрегированных файлах отсутствует поле `id`, такие записи пропускаются (это ожидаемое поведение).

## 3) Экспорт в общую папку shared-data

Команда экспорта (Django management):

```bash
docker compose -f docker-compose.prod.yml exec parser-service \
  python manage.py export_to_shared --output-dir /shared-data --limit 200
```

Результат:
- Будет создан файл вида `exported_properties_YYYYMMDD_HHMMSS.json` и симлинк `latest_export.json` в `/shared-data` (на хосте — в `./shared-data`).

Тонкости:
- На Windows симлинк может не создаться — в этом случае увидите предупреждение; сам файл экспорта при этом создаётся.
- Если экспорт вернул `0 properties`, значит в БД парсера нет подходящих объектов (часто из‑за фильтров дат или неполных полей). Уберите `--recent-days`, увеличьте объём скрейпа и повторите импорт.

## 4) Проверка связи с основным бэкендом

Поднимите зависимости и API (при необходимости установить переменные окружения):

```bash
$env:POSTGRES_PASSWORD="postgres"; $env:API_SECRET_KEY="dev"
docker compose -f docker-compose.prod.yml up -d postgres redis api-service
```

Проверка здоровья API:

```bash
curl.exe -s -i http://localhost:8000/health/
```

Проверка маунта `shared-data` внутри `api-service`:

```bash
docker compose -f docker-compose.prod.yml exec api-service ls -la /shared-data
```

Импорт данных в основной бэкенд (dry-run для проверки формата):

```bash
docker compose -f docker-compose.prod.yml exec api-service \
  python manage.py import_properties_enhanced /shared-data/latest_export.json --dry-run
``;

Для фактической загрузки уберите `--dry-run`. При необходимости используйте флаги очистки: `--wipe-sale`, `--wipe-rent`, `--wipe-areas`, `--wipe-buildings`.

## Типичные проблемы и решения

- PowerShell алиас `curl` ломает пайпы и вывод — используйте `curl.exe`.
- `no such table: properties_property` при экспорте из парсера — выполните миграции:
  ```bash
  docker compose -f docker-compose.prod.yml exec parser-service python manage.py migrate --noinput
  ```
- Переменные окружения для compose (`POSTGRES_PASSWORD`, `API_SECRET_KEY`, `PARSER_SECRET_KEY`) должны быть заданы перед `up -d`.
- Экспортные поля:
  - В экспортной команде исправлено поле верификации: используется `prop.verified`.
  - Поле площади в экспорте — `sizeMin` — формируется из известных полей объекта. Если в модели используются `area_sqm/area_sqft`, значение рассчитывается соответствующим образом (при отсутствии — оставляется пустым).

## Критерии готовности
- `/health` для `parser-service` возвращает 200 OK.
- В `shared-data/` на хосте появился JSON с экспортом.
- `api-service` видит файлы в `/shared-data` и может выполнить пробный импорт `--dry-run` без ошибок.

## Артефакты (что сохранить при проверке)
- Логи выполнения команд (скрейп, импорт, экспорт).
- Список файлов в `shared-data/` (`dir shared-data` на Windows или `ls -la shared-data` на Unix).



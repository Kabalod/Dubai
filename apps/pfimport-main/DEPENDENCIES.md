# PFImport Dependencies

Проверка зависимостей:
- Если используется `requirements.txt`: `pip install -r requirements.txt && pip check`
- Рекомендуется перейти на `requirements.in` + pip-tools по аналогии с backend

CI:
- Добавить отдельную джобу при необходимости, либо встроить в общий deps-verify


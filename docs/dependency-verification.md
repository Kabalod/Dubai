# Верификация зависимостей (Backend)

Цель: ловить конфликты версий до деплоя.

## Инструменты
- pip-tools (pip-compile) — фиксирует граф зависимостей в lock-файл
- pip check — проверяет совместимость установленных пакетов

## Поток
1. Редактируйте высокоуровневые зависимости в `apps/realty-main/requirements.in`
2. CI (workflow `deps-verify.yml`) компилирует lock: `requirements.compiled.txt`
3. Устанавливает по lock и запускает `pip check`
4. Сравнивает с коммитнутым `requirements.txt` (информативно)

## Локально
```bash
pip install pip-tools
cd apps/realty-main
pip-compile -o requirements.compiled.txt requirements.in
pip install -r requirements.compiled.txt --no-deps --require-hashes
pip check
```

Рекомендация: хранить `requirements.compiled.txt` как lock-файл (или переименовать в `requirements.lock.txt`) и использовать его в Docker.


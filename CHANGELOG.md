# Журнал изменений (Changelog)

Все заметные изменения в этом проекте будут задокументированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
и этот проект придерживается [Семантического Версионирования](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- Удалены устаревшие и дублирующиеся скрипты запуска и управления (`start-*.ps1`, `start-*.bat`, `project-manager.*`, `simple-*.*`) в пользу единого `Taskfile.yml`.
- Удалены старые Dockerfile (`apps/realty-main/Dockerfile.simple`, `apps/realty-main/deploy/Dockerfile.binary`), оставлены только актуальные.
- Удален `docs/lint-docs.sh` (используется версия для PowerShell).

### Added
- Создан `CHANGELOG.md` для отслеживания истории изменений проекта.

### Changed
- Скрипт `auto_import.sh` перенесен в `apps/realty-main/scripts/` для лучшей инкапсуляции.
- Централизовано управление задачами проекта через `Taskfile.yml`.

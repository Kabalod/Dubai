# 🔧 Настройка окружения разработки - Dubai Platform

## Требования к системе

### Минимальные требования
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **RAM**: 8 GB (рекомендуется 16 GB)
- **Storage**: 20 GB свободного места
- **Docker**: Docker Desktop 4.0+ или Docker Engine 20.10+

### Рекомендуемые требования
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **RAM**: 16 GB или больше
- **Storage**: 50 GB свободного места (для ML моделей)
- **Docker**: Docker Desktop 4.20+ с WSL2 (Windows)

## 🚀 Установка основных компонентов

### 1. Docker и Docker Compose

#### Windows
```bash
## Скачайте Docker Desktop с официального сайта
## https://www.docker.com/products/docker-desktop/

## Установите и перезагрузите систему
## Включите WSL2 в настройках Docker Desktop
```

#### macOS
```bash
## Скачайте Docker Desktop для Mac
## https://www.docker.com/products/docker-desktop/

## Установите и запустите
## Docker Desktop автоматически настроит все необходимое
```

#### Linux (Ubuntu/Debian)
```bash
## Установка Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

## Добавление пользователя в группу docker
sudo usermod -aG docker $USER

## Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

## Перезагрузка системы
sudo reboot
```

### 2. Git
```bash
## Windows: Скачайте с https://git-scm.com/
## macOS: brew install git
## Linux: sudo apt-get install git

## Проверка установки
git --version
```

### 3. Node.js (для Frontend разработки)
```bash
## Windows: Скачайте с https://nodejs.org/
## macOS: brew install node
## Linux: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -

## Проверка установки
node --version
npm --version
```

### 4. Python (для Backend разработки)
```bash
## Windows: Скачайте с https://www.python.org/
## macOS: brew install python@3.12
## Linux: sudo apt-get install python3.12 python3.12-venv

## Проверка установки
python --version
pip --version
```

## 🔧 Настройка проекта

### 1. Клонирование репозитория
```bash
## Клонирование основного репозитория
git clone <repository-url>
cd Dubai

## Клонирование подмодулей (если есть)
git submodule update --init --recursive
```

### 2. Настройка переменных окружения
```bash
## Копирование примеров
cp services/project-launcher/env.example services/project-launcher/.env
cp global-ports.env.example global-ports.env

## Редактирование файлов
## Windows
notepad services/project-launcher/.env
notepad global-ports.env

## macOS/Linux
nano services/project-launcher/.env
nano global-ports.env
```

### 3. Основные настройки .env
```env
## Project Launcher
PROJECT_LAUNCHER_PORT=8000
FRONTEND_PORT=3000
BACKEND_PORT=8000
MEMORY_LLM_PORT=8080

## База данных
DATABASE_URL=postgresql://launcher:launcher@localhost:5434/launcher
POSTGRES_PASSWORD=your-secure-password

## Безопасность
SECRET_KEY=your-secret-key-here
DEBUG=True

## AI API ключи
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 🏗️ Запуск для разработки

### 1. Первый запуск
```bash
## Запуск Project Launcher
cd services/project-launcher
docker compose up -d

## Проверка статуса
docker ps

## Открытие веб-интерфейса
## http://localhost:80
```

### 2. Запуск всех сервисов
```bash
## Возврат в корень проекта
cd ../..

## Запуск всех проектов
docker compose -f docker-compose.all-projects.yml up -d

## Или через скрипт (Windows)
./start-all-with-memory.bat
```

### 3. Проверка работоспособности
```bash
## Проверка статуса всех сервисов
docker ps

## Проверка health endpoints
curl http://localhost:80/health
curl http://localhost:3000/health
curl http://localhost:8000/health/
curl http://localhost:8080/health
```

## 🔍 Разработка отдельных компонентов

### 1. Frontend разработка (DXB-frontend-develop)
```bash
cd DXB-frontend-develop

## Установка зависимостей
npm install

## Запуск в режиме разработки
npm run dev

## Сборка для production
npm run build

## Тестирование
npm run test
npm run test:e2e
```

### 2. Backend разработка (realty-main)
```bash
cd realty-main

## Создание виртуального окружения
python -m venv venv

## Активация окружения
## Windows
venv\Scripts\activate

## macOS/Linux
source venv/bin/activate

## Установка зависимостей
pip install -r requirements.txt

## Применение миграций
python manage.py migrate

## Создание суперпользователя
python manage.py createsuperuser

## Запуск сервера разработки
python manage.py runserver
```

### 3. AI агенты разработка
```bash
cd compose-for-agents/adk

## Установка зависимостей
pip install -r requirements.txt

## Запуск агента
python agent.py

## Тестирование
python -m pytest tests/
```

### 4. Memory LLM разработка
```bash
cd Java_Memory_LLM-master

## Сборка Java проекта
./mvnw clean install

## Запуск через Docker
docker compose -f docker-compose.monitoring.yml up -d

## Проверка API
curl http://localhost:8080/health
```

## 🧪 Тестирование

### 1. Unit тесты
```bash
## Frontend тесты
cd DXB-frontend-develop
npm run test

## Backend тесты
cd realty-main
python manage.py test

## AI агенты тесты
cd compose-for-agents/adk
python -m pytest tests/
```

### 2. Integration тесты
```bash
## Запуск всех сервисов
docker compose -f docker-compose.all-projects.yml up -d

## Запуск тестов
cd tests/integration
python -m pytest
```

### 3. E2E тесты
```bash
## Frontend E2E
cd DXB-frontend-develop
npm run test:e2e

## Backend E2E
cd realty-main
python manage.py test --tag=e2e
```

## 📊 Мониторинг разработки

### 1. Логи в реальном времени
```bash
## Логи всех сервисов
docker compose -f docker-compose.all-projects.yml logs -f

## Логи конкретного сервиса
docker logs -f dxb-frontend
docker logs -f realty-main-web
docker logs -f project-launcher
```

### 2. Метрики и производительность
```bash
## Открытие Grafana
## http://localhost:3003 (admin/admin)

## Открытие Prometheus
## http://localhost:9090

## Открытие Kibana
## http://localhost:5601
```

### 3. Health checks
```bash
## Проверка всех health endpoints
curl http://localhost:80/health
curl http://localhost:3000/health
curl http://localhost:8000/health/
curl http://localhost:8080/health
```

## 🔧 Полезные инструменты разработки

### 1. VS Code расширения
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json",
    "ms-azuretools.vscode-docker",
    "ms-vscode.vscode-yaml"
  ]
}
```

### 2. Git hooks
```bash
## Установка pre-commit hooks
pip install pre-commit
pre-commit install

## Проверка кода перед коммитом
pre-commit run --all-files
```

### 3. Линтеры и форматтеры
```bash
## Python
pip install black isort flake8 mypy
black src/
isort src/
flake8 src/
mypy src/

## TypeScript/JavaScript
npm install -g eslint prettier
eslint src/ --fix
prettier --write src/
```

## 🚨 Решение проблем разработки

### 1. Проблемы с Docker
```bash
## Очистка системы
docker system prune -a
docker volume prune

## Перезапуск Docker Desktop
## Windows: Restart Docker Desktop
## macOS: Restart Docker Desktop
## Linux: sudo systemctl restart docker
```

### 2. Проблемы с портами
```bash
## Проверка занятых портов
## Windows
netstat -ano | findstr :3000

## macOS/Linux
lsof -i :3000

## Остановка процессов
## Windows
taskkill /PID <PID> /F

## macOS/Linux
kill -9 <PID>
```

### 3. Проблемы с зависимостями
```bash
## Очистка npm кэша
npm cache clean --force

## Очистка pip кэша
pip cache purge

## Переустановка зависимостей
rm -rf node_modules package-lock.json
npm install
```

## 🔗 Полезные ссылки

- [Основная документация](../README.md)
- [Quick Start Guide](../deployment/quick-start.md)
- [Архитектура](../architecture/overview.md)
- [Troubleshooting](../troubleshooting/common-issues.md)
- [API документация](../api/overview.md)

---

**Версия**: 1.0.0  
**Последнее обновление**: {{ date }}  
**Статус**: Активная разработка


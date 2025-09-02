# Комплексная проверка всего проекта DUBAI_MVP
# Проверяет все зависимости, настройки и потенциальные ошибки

param(
    [switch]$AutoFix = $false,
    [switch]$Verbose = $false
)

Write-Host "🔍 КОМПЛЕКСНАЯ ПРОВЕРКА ПРОЕКТА DUBAI_MVP" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

$errors = @()
$warnings = @()
$fixes = @()

# 1. ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА
Write-Host "`n📁 Проверка структуры проекта..." -ForegroundColor Cyan

$requiredFiles = @(
    "apps/realty-main/Dockerfile",
    "apps/realty-main/realty/settings_railway.py",
    "apps/realty-main/realty/api/views.py",
    "apps/realty-main/realty/api/urls.py",
    "apps/realty-main/realty/api/models.py",
    "apps/DXB-frontend-develop/Dockerfile",
    "apps/DXB-frontend-develop/package.json"
)

foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $errors += "❌ Отсутствует файл: $file"
    } else {
        Write-Host "✅ $file" -ForegroundColor Green
    }
}

# 2. АНАЛИЗ ЗАВИСИМОСТЕЙ В PYTHON
Write-Host "`n🐍 Анализ Python зависимостей..." -ForegroundColor Cyan

$pythonFiles = Get-ChildItem -Path "apps/realty-main" -Recurse -Filter "*.py" | Where-Object { $_.Name -ne "__pycache__" }
$allImports = @()

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -ErrorAction SilentlyContinue
    if ($content) {
        $imports = $content | Select-String "^from ([a-zA-Z_][a-zA-Z0-9_\.]*)" | ForEach-Object { 
            $_.Matches[0].Groups[1].Value 
        }
        $imports += $content | Select-String "^import ([a-zA-Z_][a-zA-Z0-9_\.]*)" | ForEach-Object { 
            $_.Matches[0].Groups[1].Value 
        }
        $allImports += $imports
    }
}

# Список известных проблемных модулей
$problematicModules = @(
    "falco", "django_litestream", "django_tasks", "django_lifecycle", 
    "django_extensions", "django_health_check", "strawberry_django",
    "unique_user_email", "crispy_forms", "crispy_tailwind", "debug_toolbar",
    "allauth", "diskcache", "dateutil", "sentry_sdk"
)

$dockerfilePath = "apps/realty-main/Dockerfile"
$dockerfileContent = Get-Content $dockerfilePath -Raw

Write-Host "🔍 Найденные импорты в коде:" -ForegroundColor Yellow
$uniqueImports = $allImports | Sort-Object | Get-Unique | Where-Object { $_ -and $_.Length -gt 0 }

foreach ($import in $uniqueImports) {
    $isProblematic = $problematicModules | Where-Object { $import.StartsWith($_) }
    if ($isProblematic) {
        if ($dockerfileContent -notmatch $isProblematic) {
            $errors += "❌ Модуль '$import' используется в коде, но отсутствует в Dockerfile"
        } else {
            Write-Host "⚠️  $import (в Dockerfile)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✅ $import" -ForegroundColor Green
    }
}

# 3. ПРОВЕРКА DJANGO SETTINGS
Write-Host "`n⚙️ Проверка Django настроек..." -ForegroundColor Cyan

$settingsPath = "apps/realty-main/realty/settings.py"
$settingsContent = Get-Content $settingsPath -Raw

# Проверка INSTALLED_APPS
$installedAppsMatch = [regex]::Match($settingsContent, 'INSTALLED_APPS\s*=\s*LOCAL_APPS\s*\+\s*THIRD_PARTY_APPS\s*\+\s*DJANGO_APPS')
if ($installedAppsMatch.Success) {
    Write-Host "✅ INSTALLED_APPS структура корректна" -ForegroundColor Green
} else {
    $warnings += "⚠️ Нестандартная структура INSTALLED_APPS"
}

# Проверка проблемных ссылок
$problematicRefs = @(
    "falco\.db_routers\.DBTaskRouter",
    "from falco",
    "import falco",
    "from realty\.pfimport",
    "from realty\.reports",
    "from realty\.building_reports"
)

foreach ($ref in $problematicRefs) {
    if ($settingsContent -match $ref) {
        $errors += "❌ Найдена проблемная ссылка в settings.py: $ref"
    }
}

# 4. ПРОВЕРКА API VIEWS
Write-Host "`n🌐 Проверка API views..." -ForegroundColor Cyan

$viewsPath = "apps/realty-main/realty/api/views.py"
$viewsContent = Get-Content $viewsPath -Raw

# Проверка импортов в views
$problematicViewImports = @(
    "from realty\.pfimport\.models",
    "from realty\.reports\.models",
    "PFListSale", "PFListRent", "BuildingReport"
)

foreach ($import in $problematicViewImports) {
    if ($viewsContent -match $import -and $viewsContent -notmatch "#.*$import") {
        $errors += "❌ Проблемный импорт в views.py: $import"
    }
}

# Проверка health_check функции
if ($viewsContent -match "def health_check") {
    Write-Host "✅ health_check endpoint найден" -ForegroundColor Green
} else {
    $errors += "❌ Отсутствует health_check endpoint"
}

# 5. ПРОВЕРКА FRONTEND
Write-Host "`n⚛️ Проверка Frontend..." -ForegroundColor Cyan

$frontendPackageJson = "apps/DXB-frontend-develop/package.json"
if (Test-Path $frontendPackageJson) {
    $packageContent = Get-Content $frontendPackageJson | ConvertFrom-Json
    Write-Host "✅ Frontend package.json найден" -ForegroundColor Green
    Write-Host "   Название: $($packageContent.name)" -ForegroundColor White
    Write-Host "   Версия: $($packageContent.version)" -ForegroundColor White
} else {
    $errors += "❌ Отсутствует frontend package.json"
}

# 6. ПРОВЕРКА DOCKER КОНФИГУРАЦИИ
Write-Host "`n🐳 Проверка Docker конфигурации..." -ForegroundColor Cyan

# Backend Dockerfile
if ($dockerfileContent -match "FROM python:3\.11-slim") {
    Write-Host "✅ Backend Dockerfile использует Python 3.11-slim" -ForegroundColor Green
} else {
    $warnings += "⚠️ Backend Dockerfile не использует рекомендуемый Python 3.11-slim"
}

if ($dockerfileContent -match "pip install.*psycopg\[binary\]") {
    Write-Host "✅ PostgreSQL драйвер установлен" -ForegroundColor Green
} else {
    $errors += "❌ Отсутствует psycopg[binary] в Dockerfile"
}

# Frontend Dockerfile
$frontendDockerfile = "apps/DXB-frontend-develop/Dockerfile"
if (Test-Path $frontendDockerfile) {
    $frontendDockerContent = Get-Content $frontendDockerfile -Raw
    if ($frontendDockerContent -match "yarn install" -or $frontendDockerContent -match "npm install") {
        Write-Host "✅ Frontend Dockerfile настроен для сборки" -ForegroundColor Green
    } else {
        $warnings += "⚠️ Frontend Dockerfile может быть неполным"
    }
}

# 7. ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ
Write-Host "`n💡 Генерация рекомендаций..." -ForegroundColor Cyan

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "🎉 ПРОЕКТ В ОТЛИЧНОМ СОСТОЯНИИ!" -ForegroundColor Green
    Write-Host "Все проверки пройдены успешно." -ForegroundColor Green
} else {
    Write-Host "`n📋 ОТЧЁТ О ПРОБЛЕМАХ:" -ForegroundColor Red
    
    if ($errors.Count -gt 0) {
        Write-Host "`n🚨 КРИТИЧЕСКИЕ ОШИБКИ ($($errors.Count)):" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️ ПРЕДУПРЕЖДЕНИЯ ($($warnings.Count)):" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    }
}

# 8. АВТОМАТИЧЕСКИЕ ИСПРАВЛЕНИЯ
if ($AutoFix -and $errors.Count -gt 0) {
    Write-Host "`n🔧 АВТОМАТИЧЕСКИЕ ИСПРАВЛЕНИЯ..." -ForegroundColor Magenta
    
    # Здесь можно добавить логику автоматических исправлений
    Write-Host "Функция автоисправлений будет добавлена в следующей версии" -ForegroundColor Yellow
}

# 9. ИТОГОВАЯ СТАТИСТИКА
Write-Host "`n📊 ИТОГОВАЯ СТАТИСТИКА:" -ForegroundColor Cyan
Write-Host "  Критические ошибки: $($errors.Count)" -ForegroundColor $(if ($errors.Count -eq 0) { "Green" } else { "Red" })
Write-Host "  Предупреждения: $($warnings.Count)" -ForegroundColor $(if ($warnings.Count -eq 0) { "Green" } else { "Yellow" })
Write-Host "  Проверенные файлы: $($requiredFiles.Count)" -ForegroundColor White
Write-Host "  Найденные импорты: $($uniqueImports.Count)" -ForegroundColor White

Write-Host "`n🏁 Комплексная проверка завершена!" -ForegroundColor Green

# Возврат кода ошибки для CI/CD
if ($errors.Count -gt 0) {
    exit 1
} else {
    exit 0
}

# 🔍 Dubai Project - Structure Check
# Скрипт для проверки структуры проекта в pre-commit hooks

param(
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'

# Цвета для вывода
$Colors = @{
    Red = 'Red'
    Green = 'Green'
    Yellow = 'Yellow'
    Blue = 'Blue'
    Cyan = 'Cyan'
    Default = 'White'
}

# Функции для вывода
function Write-Status {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Colors.Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $Colors.Default
}

function Write-Debug {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "🔍 $Message" -ForegroundColor $Colors.Blue
    }
}

Write-Host "🔍 Проверка структуры проекта Dubai..." -ForegroundColor Cyan

# Требуемая структура проекта
$requiredStructure = @{
    "docs" = @{
        "README.md" = $true
        "OVERVIEW.md" = $true
        "NAVIGATION.md" = $true
        "CONTRIBUTING.md" = $true
        "GPT_RULES.md" = $true
        "CURSOR_RULES.md" = $true
        "LINTING.md" = $true
        "PROJECT_STRUCTURE.md" = $true
    }
    "scripts" = @{
        "project-manager.ps1" = $true
        "project-manager.sh" = $true
        "reorganize-project.ps1" = $true
        "reorganize-project.sh" = $true
    }
    "env" = @{
        ".env.development" = $true
        ".env.production" = $true
    }
}

# Проверка структуры
function Test-ProjectStructure {
    Write-Info "📁 Проверка структуры проекта..."
    
    $totalIssues = 0
    $missingFiles = @()
    
    foreach ($directory in $requiredStructure.Keys) {
        if (-not (Test-Path $directory)) {
            Write-Error "Отсутствует директория: $directory"
            $totalIssues++
            continue
        }
        
        Write-Debug "Проверяю директорию: $directory"
        
        foreach ($file in $requiredStructure[$directory].Keys) {
            $filePath = Join-Path $directory $file
            if (-not (Test-Path $filePath)) {
                Write-Warning "Отсутствует файл: $filePath"
                $missingFiles += $filePath
                $totalIssues++
            } else {
                Write-Debug "  ✅ $file"
            }
        }
    }
    
    # Проверка дополнительных требований
    $additionalChecks = @{
        "Dockerfile" = $true
        "docker-compose.yml" = $true
        "requirements.txt" = $true
        "package.json" = $true
        "README.md" = $true
    }
    
    foreach ($file in $additionalChecks.Keys) {
        if (-not (Test-Path $file)) {
            Write-Warning "Отсутствует корневой файл: $file"
            $missingFiles += $file
            $totalIssues++
        }
    }
    
    if ($totalIssues -eq 0) {
        Write-Status "Структура проекта корректна"
        return 0
    } else {
        Write-Warning "Найдено $totalIssues проблем со структурой"
        Write-Host ""
        Write-Host "📋 Отсутствующие файлы:" -ForegroundColor Yellow
        foreach ($file in $missingFiles) {
            Write-Host "  - $file" -ForegroundColor $Colors.Yellow
        }
        return $totalIssues
    }
}

# Проверка содержимого ключевых файлов
function Test-KeyFiles {
    Write-Info "📄 Проверка содержимого ключевых файлов..."
    
    $issues = 0
    
    # Проверка README.md
    if (Test-Path "README.md") {
        $readmeContent = Get-Content "README.md" -Raw
        if ($readmeContent.Length -lt 500) {
            Write-Warning "README.md слишком короткий"
            $issues++
        }
        
        if ($readmeContent -notmatch "## Установка" -and $readmeContent -notmatch "## Быстрый старт") {
            Write-Warning "README.md не содержит раздел установки"
            $issues++
        }
    }
    
    # Проверка CONTRIBUTING.md
    if (Test-Path "docs/CONTRIBUTING.md") {
        $contributingContent = Get-Content "docs/CONTRIBUTING.md" -Raw
        if ($contributingContent -notmatch "## Процесс разработки") {
            Write-Warning "CONTRIBUTING.md не содержит процесс разработки"
            $issues++
        }
    }
    
    if ($issues -eq 0) {
        Write-Status "Содержимое ключевых файлов корректно"
    }
    
    return $issues
}

# Проверка конфигурационных файлов
function Test-ConfigFiles {
    Write-Info "⚙️  Проверка конфигурационных файлов..."
    
    $issues = 0
    
    # Проверка .pre-commit-config.yaml
    if (Test-Path ".pre-commit-config.yaml") {
        try {
            $yamlContent = Get-Content ".pre-commit-config.yaml" -Raw
            if ($yamlContent -notmatch "dubai-docs-lint") {
                Write-Warning ".pre-commit-config.yaml не содержит проверку документации"
                $issues++
            }
        } catch {
            Write-Warning "Не удалось прочитать .pre-commit-config.yaml"
            $issues++
        }
    } else {
        Write-Warning "Отсутствует .pre-commit-config.yaml"
        $issues++
    }
    
    # Проверка docker-compose.yml
    if (Test-Path "docker-compose.yml") {
        try {
            $dockerContent = Get-Content "docker-compose.yml" -Raw
            if ($dockerContent -notmatch "version:") {
                Write-Warning "docker-compose.yml не содержит версию"
                $issues++
            }
        } catch {
            Write-Warning "Не удалось прочитать docker-compose.yml"
            $issues++
        }
    }
    
    if ($issues -eq 0) {
        Write-Status "Конфигурационные файлы корректны"
    }
    
    return $issues
}

# Основная функция
function Main {
    $startTime = Get-Date
    $totalIssues = 0
    
    # Проверка структуры
    $structureIssues = Test-ProjectStructure
    $totalIssues += $structureIssues
    
    # Проверка ключевых файлов
    $keyFileIssues = Test-KeyFiles
    $totalIssues += $keyFileIssues
    
    # Проверка конфигурации
    $configIssues = Test-ConfigFiles
    $totalIssues += $configIssues
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Cyan
    if ($totalIssues -eq 0) {
        Write-Status "Проверка структуры проекта завершена успешно!"
        exit 0
    } else {
        Write-Error "Проверка структуры проекта завершена с ошибками!"
        Write-Host "Найдено $totalIssues проблем" -ForegroundColor $Colors.Red
        Write-Host ""
        Write-Host "🔧 Рекомендации:" -ForegroundColor Yellow
        Write-Host "1. Создайте отсутствующие файлы и директории" -ForegroundColor White
        Write-Host "2. Обновите содержимое ключевых файлов" -ForegroundColor White
        Write-Host "3. Проверьте конфигурацию проекта" -ForegroundColor White
        Write-Host "4. Запустите проверку снова" -ForegroundColor White
        Write-Host ""
        Write-Host "⏱️  Время выполнения: $($duration.TotalSeconds.ToString('F2')) сек" -ForegroundColor Cyan
        exit 1
    }
}

# Запуск
Main

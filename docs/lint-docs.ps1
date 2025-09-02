# 🚀 Dubai Project - Lint Documentation (PowerShell)
# Улучшенный скрипт для проверки качества документации

param(
    [switch]$Fix,
    [switch]$Verbose,
    [switch]$Test
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

# Функции для вывода с цветом
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

Write-Host "🔍 Проверка документации Dubai Project..." -ForegroundColor Cyan
Write-Host ""

# Проверка наличия markdownlint
function Test-Markdownlint {
    try {
        $null = Get-Command markdownlint -ErrorAction Stop
        Write-Status "Markdownlint найден"
        return $true
    }
    catch {
        Write-Warning "Markdownlint не найден. Установите: npm install -g markdownlint-cli"
        return $false
    }
}

# Проверка markdown файлов
function Invoke-MarkdownLint {
    if (Test-Markdownlint) {
        Write-Info "📝 Проверка Markdown файлов..."
        try {
            $result = markdownlint '**/*.md' --ignore .markdownlintignore 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Markdown линтинг завершен успешно"
            } else {
                Write-Warning "Markdown линтинг обнаружил проблемы:"
                Write-Host $result -ForegroundColor $Colors.Yellow
            }
        }
        catch {
            Write-Warning "Ошибка при выполнении markdownlint: $_"
        }
    }
    else {
        Write-Warning "Пропускаем Markdown линтинг"
    }
}

# Проверка структуры заголовков
function Test-Headers {
    Write-Info "🏷️  Проверка структуры заголовков..."
    
    $mdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object { $_.FullName -notlike "*\site\*" }
    $totalIssues = 0
    
    foreach ($file in $mdFiles) {
        $content = Get-Content $file.FullName -Raw
        $lines = $content -split "`n"
        
        $h1Count = 0
        $h2Exists = $false
        $h3Exists = $false
        $issues = @()
        
        foreach ($line in $lines) {
            if ($line -match "^# ") {
                $h1Count++
            }
            elseif ($line -match "^## ") {
                $h2Exists = $true
            }
            elseif ($line -match "^### ") {
                $h3Exists = $true
            }
        }
        
        if ($h1Count -gt 1) {
            $issues += "Найдено $h1Count H1 заголовков (должен быть только один)"
            $totalIssues++
        }
        
        if ($h1Count -eq 0) {
            $issues += "H1 заголовок отсутствует"
            $totalIssues++
        }
        
        if ($h1Count -eq 1 -and -not $h2Exists) {
            $issues += "H2 заголовки отсутствуют после H1"
            $totalIssues++
        }
        
        if ($issues.Count -gt 0) {
            Write-Warning "Файл $($file.Name):"
            foreach ($issue in $issues) {
                Write-Host "  - $issue" -ForegroundColor $Colors.Yellow
            }
        }
    }
    
    if ($totalIssues -eq 0) {
        Write-Status "Структура заголовков корректна"
    } else {
        Write-Warning "Найдено $totalIssues проблем с заголовками"
    }
    
    return $totalIssues
}

# Проверка внутренних ссылок
function Test-InternalLinks {
    Write-Info "🔗 Проверка внутренних ссылок..."
    
    $mdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object { $_.FullName -notlike "*\site\*" }
    $brokenLinks = 0
    $totalLinks = 0
    
    foreach ($file in $mdFiles) {
        try {
            $content = Get-Content $file.FullName -Raw
            # Используем простой паттерн для поиска ссылок
            $linkPattern = '\[([^\]]+)\]\(([^)]+)\)'
            $matches = [regex]::Matches($content, $linkPattern)
            
            foreach ($match in $matches) {
                $link = $match.Groups[2].Value
                $totalLinks++
                
                if ($link -match '^\./') {
                    $targetPath = Join-Path (Split-Path $file.FullName) $link.Substring(2)
                    if (-not (Test-Path $targetPath)) {
                        Write-Warning "Сломанная ссылка в $($file.Name): $link"
                        $brokenLinks++
                    }
                }
            }
        }
        catch {
            Write-Warning "Не удалось прочитать файл $($file.Name): $_"
        }
    }
    
    if ($brokenLinks -eq 0) {
        Write-Status "Все внутренние ссылки корректны"
    } else {
        Write-Warning "Найдено $brokenLinks сломанных ссылок из $totalLinks"
    }
    
    return $brokenLinks
}

# Проверка качества документации
function Test-Quality {
    Write-Info "🎯 Проверка качества документации..."
    
    $mdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object { $_.FullName -notlike "*\site\*" }
    $totalFiles = $mdFiles.Count
    $qualityScore = 0
    
    foreach ($file in $mdFiles) {
        $content = Get-Content $file.FullName -Raw
        $lines = $content -split "`n"
        
        # Проверка длины файла
        if ($lines.Count -gt 10) {
            $qualityScore += 1
        }
        
        # Проверка наличия описания
        if ($content -match "## Обзор" -or $content -match "## Описание") {
            $qualityScore += 1
        }
        
        # Проверка структуры
        if ($content -match "## " -and $content -match "### ") {
            $qualityScore += 1
        }
        
        # Проверка примеров кода
        if ($content -match "```") {
            $qualityScore += 1
        }
        
        # Проверка ссылок - используем простой паттерн
        if ($content -match '\[.*\]\(.*\)') {
            $qualityScore += 1
        }
    }
    
    $maxScore = $totalFiles * 5
    $percentage = [math]::Round(($qualityScore / $maxScore) * 100, 1)
    
    Write-Info "Качество документации: $percentage% ($qualityScore/$maxScore)"
    
    if ($percentage -ge 80) {
        Write-Status "Отличное качество документации"
    } elseif ($percentage -ge 60) {
        Write-Warning "Хорошее качество документации, есть возможности для улучшения"
    } else {
        Write-Error "Требуется улучшение качества документации"
    }
    
    return $percentage
}

# Автоматическое исправление общих проблем
function Fix-CommonIssues {
    Write-Info "🔧 Автоматическое исправление общих проблем..."
    
    $mdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object { $_.FullName -notlike "*\site\*" }
    $fixedFiles = 0
    
    foreach ($file in $mdFiles) {
        try {
            $content = Get-Content $file.FullName -Raw
            $lines = $content -split "`n"
            $modified = $false
            
            # Исправление множественных H1 заголовков
            $h1Count = 0
            $hasH2Before = $false
            
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match "^# ") {
                    $h1Count++
                    if ($h1Count -gt 1) {
                        # Проверяем, есть ли H2 перед этим H1
                        for ($j = 0; $j -lt $i; $j++) {
                            if ($lines[$j] -match "^## ") {
                                $hasH2Before = $true
                                break
                            }
                        }
                        
                        if (-not $hasH2Before) {
                            $lines[$i] = $lines[$i] -replace "^# ", "## "
                            $modified = $true
                        }
                    }
                }
            }
            
            if ($modified) {
                $content = $lines -join "`n"
            }
            
            # Сохраняем изменения
            if ($modified) {
                $content | Out-File -FilePath $file.FullName -Encoding UTF8
                Write-Status "Исправлен файл: $($file.Name)"
                $fixedFiles++
            }
        }
        catch {
            Write-Warning "Не удалось обработать файл $($file.Name): $_"
        }
    }
    
    if ($fixedFiles -eq 0) {
        Write-Status "Автоматические исправления не требуются"
    }
    else {
        Write-Status "Автоматически исправлено $fixedFiles файлов"
    }
}

# Основная функция
function Main {
    $startTime = Get-Date
    
    # Проверка структуры документации
    Test-Headers
    
    # Проверка внутренних ссылок
    Test-InternalLinks
    
    # Проверка качества
    Test-Quality
    
    # Автоматическое исправление
    if ($Fix) {
        Fix-CommonIssues
    }
    
    # Markdown линтинг
    Invoke-MarkdownLint
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Status "Проверка документации завершена!"
    Write-Host ""
    Write-Host "📚 Следующие шаги:" -ForegroundColor Yellow
    Write-Host "1. Исправьте найденные проблемы" -ForegroundColor White
    Write-Host "2. Запустите скрипт снова для проверки" -ForegroundColor White
    Write-Host "3. Следуйте правилам из CONTRIBUTING.md" -ForegroundColor White
    Write-Host "4. Используйте GPT_RULES.md для AI моделей" -ForegroundColor White
    Write-Host "5. Используйте CURSOR_RULES.md для Cursor IDE" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Использование:" -ForegroundColor Yellow
    Write-Host "  .\lint-docs.ps1          # Базовая проверка" -ForegroundColor White
    Write-Host "  .\lint-docs.ps1 -Verbose # Подробный вывод" -ForegroundColor White
    Write-Host "  .\lint-docs.ps1 -Fix     # Автоматическое исправление" -ForegroundColor White
    Write-Host "  .\lint-docs.ps1 -Test    # Тестовый режим" -ForegroundColor White
    Write-Host ""
    Write-Host "⏱️  Время выполнения: $($duration.TotalSeconds.ToString('F2')) сек" -ForegroundColor Cyan
}

# Запуск
if ($Test) {
    Write-Info "🧪 Тестовый режим - проверка функций линтера..."
    # Здесь можно добавить тесты
    Write-Status "Тестирование завершено"
} else {
    Main
}

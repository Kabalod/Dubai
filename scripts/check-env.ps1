# 🔍 Dubai Project - Environment Variables Check
# Скрипт для проверки переменных окружения в pre-commit hooks

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

Write-Host "🔍 Проверка переменных окружения Dubai Project..." -ForegroundColor Cyan

# Требуемые переменные окружения
$requiredEnvVars = @{
    "Development" = @{
        "DATABASE_URL" = "postgresql://user:pass@localhost:5432/dubai_dev"
        "REDIS_URL" = "redis://localhost:6379/0"
        "SECRET_KEY" = "your-secret-key-here"
        "DEBUG" = "True"
        "ALLOWED_HOSTS" = "localhost,127.0.0.1"
    }
    "Production" = @{
        "DATABASE_URL" = "postgresql://user:pass@db:5432/dubai_prod"
        "REDIS_URL" = "redis://redis:6379/0"
        "SECRET_KEY" = "CHANGE_ME_IN_PRODUCTION"
        "DEBUG" = "False"
        "ALLOWED_HOSTS" = "your-domain.com"
    }
}

# Проверка файлов .env
function Test-EnvFiles {
    Write-Info "📁 Проверка файлов переменных окружения..."
    
    $issues = 0
    $missingFiles = @()
    
    foreach ($env in $requiredEnvVars.Keys) {
        $envFile = "env/.env.$($env.ToLower())"
        
        if (-not (Test-Path $envFile)) {
            Write-Warning "Отсутствует файл: $envFile"
            $missingFiles += $envFile
            $issues++
        } else {
            Write-Debug "Найден файл: $envFile"
            
            # Проверка содержимого
            try {
                $envContent = Get-Content $envFile -Raw
                $envVars = @{}
                
                # Парсинг переменных
                foreach ($line in ($envContent -split "`n")) {
                    if ($line -match "^([^#][^=]+)=(.*)$") {
                        $key = $matches[1].Trim()
                        $value = $matches[2].Trim()
                        $envVars[$key] = $value
                    }
                }
                
                # Проверка требуемых переменных
                foreach ($requiredVar in $requiredEnvVars[$env].Keys) {
                    if (-not $envVars.ContainsKey($requiredVar)) {
                        Write-Warning "В $envFile отсутствует переменная: $requiredVar"
                        $issues++
                    } else {
                        $actualValue = $envVars[$requiredVar]
                        $expectedValue = $requiredEnvVars[$env][$requiredVar]
                        
                        # Проверка на placeholder значения
                        if ($actualValue -match "CHANGE_ME|your-|placeholder|example") {
                            Write-Warning "В $envFile переменная $requiredVar содержит placeholder: $actualValue"
                            $issues++
                        }
                        
                        Write-Debug "  ✅ $requiredVar = $actualValue"
                    }
                }
                
            } catch {
                Write-Warning "Не удалось прочитать $envFile: $_"
                $issues++
            }
        }
    }
    
    if ($issues -eq 0) {
        Write-Status "Файлы переменных окружения корректны"
    } else {
        Write-Warning "Найдено $issues проблем с переменными окружения"
        if ($missingFiles.Count -gt 0) {
            Write-Host ""
            Write-Host "📋 Отсутствующие файлы:" -ForegroundColor Yellow
            foreach ($file in $missingFiles) {
                Write-Host "  - $file" -ForegroundColor $Colors.Yellow
            }
        }
    }
    
    return $issues
}

# Проверка .env.example
function Test-EnvExample {
    Write-Info "📋 Проверка .env.example..."
    
    $issues = 0
    
    if (Test-Path ".env.example") {
        try {
            $exampleContent = Get-Content ".env.example" -Raw
            
            # Проверка наличия комментариев
            if ($exampleContent -notmatch "#") {
                Write-Warning ".env.example не содержит комментарии"
                $issues++
            }
            
            # Проверка наличия описания
            if ($exampleContent -notmatch "##") {
                Write-Warning ".env.example не содержит описание переменных"
                $issues++
            }
            
            # Проверка структуры
            $lines = $exampleContent -split "`n"
            $varLines = 0
            $commentLines = 0
            
            foreach ($line in $lines) {
                if ($line -match "^[^#][^=]+=") {
                    $varLines++
                } elseif ($line -match "^#") {
                    $commentLines++
                }
            }
            
            if ($varLines -eq 0) {
                Write-Warning ".env.example не содержит переменные"
                $issues++
            }
            
            if ($commentLines -eq 0) {
                Write-Warning ".env.example не содержит комментарии"
                $issues++
            }
            
            Write-Debug "Переменных: $varLines, комментариев: $commentLines"
            
        } catch {
            Write-Warning "Не удалось прочитать .env.example: $_"
            $issues++
        }
    } else {
        Write-Warning "Отсутствует .env.example"
        $issues++
    }
    
    if ($issues -eq 0) {
        Write-Status ".env.example корректен"
    }
    
    return $issues
}

# Проверка безопасности
function Test-Security {
    Write-Info "🔒 Проверка безопасности переменных окружения..."
    
    $issues = 0
    
    # Проверка на наличие секретов в коде
    $sensitivePatterns = @(
        "password.*=.*['\""][^'\""]+['\""]",
        "secret.*=.*['\""][^'\""]+['\""]",
        "key.*=.*['\""][^'\""]+['\""]",
        "token.*=.*['\""][^'\""]+['\""]"
    )
    
    $codeFiles = @(
        "*.py", "*.js", "*.ts", "*.java", "*.yml", "*.yaml"
    )
    
    foreach ($pattern in $codeFiles) {
        $files = Get-ChildItem -Path . -Filter $pattern -Recurse | Where-Object { 
            $_.FullName -notlike "*\node_modules\*" -and 
            $_.FullName -notlike "*\venv\*" -and
            $_.FullName -notlike "*\__pycache__\*"
        }
        
        foreach ($file in $files) {
            try {
                $content = Get-Content $file.FullName -Raw
                
                foreach ($sensitivePattern in $sensitivePatterns) {
                    if ($content -match $sensitivePattern) {
                        Write-Warning "Возможный секрет в $($file.Name): $($matches[0])"
                        $issues++
                    }
                }
            } catch {
                # Игнорируем ошибки чтения
            }
        }
    }
    
    if ($issues -eq 0) {
        Write-Status "Проверка безопасности пройдена"
    } else {
        Write-Warning "Найдено $issues потенциальных проблем безопасности"
    }
    
    return $issues
}

# Основная функция
function Main {
    $startTime = Get-Date
    $totalIssues = 0
    
    # Проверка файлов .env
    $envIssues = Test-EnvFiles
    $totalIssues += $envIssues
    
    # Проверка .env.example
    $exampleIssues = Test-EnvExample
    $totalIssues += $exampleIssues
    
    # Проверка безопасности
    $securityIssues = Test-Security
    $totalIssues += $securityIssues
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Cyan
    if ($totalIssues -eq 0) {
        Write-Status "Проверка переменных окружения завершена успешно!"
        exit 0
    } else {
        Write-Error "Проверка переменных окружения завершена с ошибками!"
        Write-Host "Найдено $totalIssues проблем" -ForegroundColor $Colors.Red
        Write-Host ""
        Write-Host "🔧 Рекомендации:" -ForegroundColor Yellow
        Write-Host "1. Создайте отсутствующие .env файлы" -ForegroundColor White
        Write-Host "2. Добавьте все требуемые переменные" -ForegroundColor White
        Write-Host "3. Замените placeholder значения на реальные" -ForegroundColor White
        Write-Host "4. Проверьте безопасность переменных" -ForegroundColor White
        Write-Host "5. Запустите проверку снова" -ForegroundColor White
        Write-Host ""
        Write-Host "⏱️  Время выполнения: $($duration.TotalSeconds.ToString('F2')) сек" -ForegroundColor Cyan
        exit 1
    }
}

# Запуск
Main

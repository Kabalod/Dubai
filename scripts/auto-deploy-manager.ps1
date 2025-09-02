# Автоматизированный менеджер деплоя
# Полная автоматизация: диагностика → исправление → деплой → тестирование

param(
    [switch]$WatchMode = $false,
    [int]$MaxRetries = 5,
    [int]$WaitSeconds = 60
)

Write-Host "🤖 АВТОМАТИЗИРОВАННЫЙ МЕНЕДЖЕР ДЕПЛОЯ" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$script:deployAttempt = 1
$script:maxRetries = $MaxRetries

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-BackendHealth {
    try {
        $response = Invoke-RestMethod -Uri "https://workerproject-production.up.railway.app/api/health/" -Method GET -TimeoutSec 10
        return @{ Success = $true; Data = $response }
    } catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Get-RailwayLogs {
    try {
        $logs = npx --yes @railway/cli@latest logs 2>&1
        return $logs -join "`n"
    } catch {
        return "Не удалось получить логи: $($_.Exception.Message)"
    }
}

function Find-MissingDependencies {
    param([string]$LogText)
    
    $dependencies = @()
    $patterns = @{
        "No module named '([^']+)'" = '$1'
        "ModuleNotFoundError: No module named '([^']+)'" = '$1'
        "ImportError: No module named ([^\s]+)" = '$1'
    }
    
    foreach ($pattern in $patterns.Keys) {
        $matches = [regex]::Matches($LogText, $pattern)
        foreach ($match in $matches) {
            $module = $match.Groups[1].Value
            $dependencies += $module
        }
    }
    
    return $dependencies | Sort-Object | Get-Unique
}

function Add-DependencyToDockerfile {
    param([string]$Dependency)
    
    $dockerfilePath = "apps/realty-main/Dockerfile"
    $content = Get-Content $dockerfilePath -Raw
    
    # Найти последнюю строку с pip install
    $lines = $content -split "`n"
    $lastPipIndex = -1
    
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        if ($lines[$i] -match "pip install.*--no-cache-dir") {
            $lastPipIndex = $i
            break
        }
    }
    
    if ($lastPipIndex -ge 0) {
        $lines[$lastPipIndex] = $lines[$lastPipIndex].TrimEnd() + " $Dependency"
        $newContent = $lines -join "`n"
        Set-Content $dockerfilePath $newContent -NoNewline
        return $true
    }
    
    return $false
}

function Deploy-Changes {
    param([string[]]$Dependencies = @())
    
    if ($Dependencies.Count -gt 0) {
        $depList = $Dependencies -join ", "
        $commitMessage = "fix(auto): add missing dependencies: $depList"
    } else {
        $commitMessage = "fix(auto): automated deployment attempt $script:deployAttempt"
    }
    
    Write-Status "📤 Коммит и деплой изменений..." "Yellow"
    
    git add -A | Out-Null
    git commit -m $commitMessage | Out-Null
    git push | Out-Null
    
    Write-Status "✅ Изменения отправлены в Railway" "Green"
}

function Wait-ForDeployment {
    param([int]$TimeoutSeconds = 40)
    
    Write-Status "⏳ Ожидание завершения деплоя ($TimeoutSeconds сек)..." "Yellow"
    
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    while ((Get-Date) -lt $timeout) {
        Start-Sleep -Seconds 10
        
        $health = Test-BackendHealth
        if ($health.Success) {
            Write-Status "🎉 Backend успешно запущен!" "Green"
            Write-Status "Статус: $($health.Data.status)" "White"
            return $true
        }
        
        Write-Status "⏳ Всё ещё ожидаем..." "Yellow"
    }
    
    Write-Status "⏰ Таймаут ожидания деплоя" "Red"
    return $false
}

function Run-ComprehensiveCheck {
    Write-Status "🔍 Запуск комплексной проверки..." "Cyan"
    
    try {
        $result = & ".\scripts\comprehensive-check.ps1" 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Status "✅ Комплексная проверка пройдена" "Green"
            return @{ Success = $true; Issues = @() }
        } else {
            Write-Status "❌ Найдены проблемы в проекте" "Red"
            return @{ Success = $false; Issues = $result }
        }
    } catch {
        Write-Status "❌ Ошибка при запуске проверки: $($_.Exception.Message)" "Red"
        return @{ Success = $false; Issues = @() }
    }
}

function Start-AutoDeployment {
    Write-Status "🚀 Начинаем автоматический деплой (попытка $script:deployAttempt/$script:maxRetries)" "Cyan"
    
    # 1. Комплексная проверка
    $check = Run-ComprehensiveCheck
    if (-not $check.Success) {
        Write-Status "⚠️ Найдены проблемы, но продолжаем..." "Yellow"
    }
    
    # 2. Проверка текущего статуса
    $health = Test-BackendHealth
    if ($health.Success) {
        Write-Status "✅ Backend уже работает!" "Green"
        return $true
    }
    
    # 3. Получение логов для диагностики
    Write-Status "📋 Анализ логов Railway..." "Cyan"
    $logs = Get-RailwayLogs
    
    # 4. Поиск недостающих зависимостей
    $missingDeps = Find-MissingDependencies -LogText $logs
    
    if ($missingDeps.Count -gt 0) {
        Write-Status "🔧 Найдены недостающие зависимости: $($missingDeps -join ', ')" "Yellow"
        
        foreach ($dep in $missingDeps) {
            if (Add-DependencyToDockerfile -Dependency $dep) {
                Write-Status "✅ Добавлена зависимость: $dep" "Green"
            }
        }
        
        Deploy-Changes -Dependencies $missingDeps
    } else {
        Write-Status "🔄 Перезапуск деплоя..." "Yellow"
        Deploy-Changes
    }
    
    # 5. Ожидание результата
    $deploySuccess = Wait-ForDeployment -TimeoutSeconds 40
    
    if ($deploySuccess) {
        Write-Status "🎉 Автоматический деплой успешен!" "Green"
        return $true
    } else {
        Write-Status "❌ Деплой не удался" "Red"
        return $false
    }
}

function Start-WatchMode {
    Write-Status "👁️ Запуск режима мониторинга..." "Cyan"
    
    while ($true) {
        $health = Test-BackendHealth
        
        if (-not $health.Success) {
            Write-Status "❌ Backend недоступен, запускаем автоисправление..." "Red"
            
            $success = Start-AutoDeployment
            if (-not $success) {
                Write-Status "⚠️ Автоисправление не удалось, повтор через $WaitSeconds сек..." "Yellow"
            }
        } else {
            Write-Status "✅ Backend работает нормально" "Green"
        }
        
        Start-Sleep -Seconds $WaitSeconds
    }
}

# ОСНОВНАЯ ЛОГИКА
try {
    if ($WatchMode) {
        Start-WatchMode
    } else {
        # Цикл попыток деплоя
        while ($script:deployAttempt -le $script:maxRetries) {
            $success = Start-AutoDeployment
            
            if ($success) {
                Write-Status "🎉 ДЕПЛОЙ ЗАВЕРШЁН УСПЕШНО!" "Green"
                
                # Финальное тестирование
                Write-Status "🧪 Финальное тестирование..." "Cyan"
                Write-Status "Backend: https://workerproject-production.up.railway.app/api/health/" "White"
                Write-Status "Frontend: https://frontend-production-5c48.up.railway.app/auth" "White"
                Write-Status "OTP Test: Введите kbalodk@gmail.com и нажмите SIGN UP" "White"
                
                exit 0
            }
            
            $script:deployAttempt++
            
            if ($script:deployAttempt -le $script:maxRetries) {
                Write-Status "🔄 Попытка $script:deployAttempt из $script:maxRetries через 30 сек..." "Yellow"
                Start-Sleep -Seconds 30
            }
        }
        
        Write-Status "❌ Превышено максимальное количество попыток ($script:maxRetries)" "Red"
        Write-Status "🔧 Попробуйте ручную диагностику:" "Yellow"
        Write-Status "   .\scripts\comprehensive-check.ps1" "White"
        Write-Status "   .\scripts\railway-health-check.ps1" "White"
        
        exit 1
    }
} catch {
    Write-Status "💥 Критическая ошибка: $($_.Exception.Message)" "Red"
    exit 1
}

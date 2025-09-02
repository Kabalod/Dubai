# Railway Log Monitor - автоматический мониторинг логов и исправление ошибок зависимостей
# Использование: .\scripts\railway-monitor.ps1

Write-Host "🚀 Railway Backend Monitor" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Функция проверки статуса backend
function Test-BackendHealth {
    try {
        $response = Invoke-RestMethod -Uri "https://workerproject-production.up.railway.app/api/health/" -TimeoutSec 10
        return $true
    }
    catch {
        return $false
    }
}

# Функция получения логов Railway
function Get-RailwayLogs {
    Write-Host "📋 Получение логов Railway..." -ForegroundColor Yellow
    try {
        $logs = npx --yes @railway/cli@latest logs --json 2>$null
        return $logs
    }
    catch {
        Write-Host "❌ Ошибка получения логов Railway" -ForegroundColor Red
        return $null
    }
}

# Функция анализа ошибок зависимостей
function Find-MissingDependencies {
    param($logs)
    
    $missingDeps = @()
    
    # Паттерны для поиска недостающих зависимостей
    $patterns = @{
        "ModuleNotFoundError: No module named '(.+)'" = "pip install {0}"
        "ImportError: No module named (.+)" = "pip install {0}"
        "Could not find backend '(.+)'" = "pip install {0}"
    }
    
    foreach ($line in $logs -split "`n") {
        foreach ($pattern in $patterns.Keys) {
            if ($line -match $pattern) {
                $module = $matches[1].Trim("'`"")
                $missingDeps += @{
                    Module = $module
                    Command = $patterns[$pattern] -f $module
                    Line = $line.Trim()
                }
            }
        }
    }
    
    return $missingDeps
}

# Функция автоматического добавления зависимостей
function Add-MissingDependency {
    param($module)
    
    Write-Host "🔧 Добавление зависимости: $module" -ForegroundColor Green
    
    # Читаем текущий Dockerfile
    $dockerfilePath = "apps\realty-main\Dockerfile"
    $content = Get-Content $dockerfilePath -Raw
    
    # Добавляем зависимость в последнюю строку pip install
    $newContent = $content -replace '(pip install --no-cache-dir [^&]+)', "`$1 $module"
    
    # Сохраняем изменения
    Set-Content $dockerfilePath $newContent -NoNewline
    
    # Коммитим и пушим
    git add -A
    git commit -m "fix(deps): auto-add missing dependency $module"
    git push
    
    Write-Host "✅ Зависимость $module добавлена и запушена" -ForegroundColor Green
}

# Основной цикл мониторинга
Write-Host "🔍 Начинаем мониторинг..." -ForegroundColor Yellow

$attempts = 0
$maxAttempts = 10

while ($attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "`n--- Попытка $attempts/$maxAttempts ---" -ForegroundColor Cyan
    
    # Проверяем статус backend
    if (Test-BackendHealth) {
        Write-Host "✅ Backend работает! Проверьте:" -ForegroundColor Green
        Write-Host "   🔗 Health: https://workerproject-production.up.railway.app/api/health/" -ForegroundColor White
        Write-Host "   🔗 Frontend: https://frontend-production-5c48.up.railway.app/auth" -ForegroundColor White
        break
    }
    
    Write-Host "❌ Backend не отвечает, анализируем логи..." -ForegroundColor Red
    
    # Получаем логи
    $logs = Get-RailwayLogs
    if (-not $logs) {
        Write-Host "⚠️  Не удалось получить логи, ждём 30 секунд..." -ForegroundColor Yellow
        Start-Sleep 30
        continue
    }
    
    # Ищем недостающие зависимости
    $missingDeps = Find-MissingDependencies $logs
    
    if ($missingDeps.Count -gt 0) {
        Write-Host "🔍 Найдены недостающие зависимости:" -ForegroundColor Yellow
        foreach ($dep in $missingDeps) {
            Write-Host "   📦 $($dep.Module)" -ForegroundColor White
            Write-Host "   📝 $($dep.Line)" -ForegroundColor Gray
        }
        
        # Добавляем первую найденную зависимость
        $firstDep = $missingDeps[0]
        Add-MissingDependency $firstDep.Module
        
        Write-Host "⏳ Ждём пересборки Railway (3 минуты)..." -ForegroundColor Yellow
        Start-Sleep 180
    }
    else {
        Write-Host "❓ Зависимости не найдены, показываем последние логи:" -ForegroundColor Yellow
        Write-Host $logs.Split("`n")[-10..-1] -ForegroundColor Gray
        Start-Sleep 30
    }
}

if ($attempts -ge $maxAttempts) {
    Write-Host "❌ Превышено максимальное количество попыток" -ForegroundColor Red
    Write-Host "🔗 Проверьте логи вручную: https://railway.app/" -ForegroundColor Yellow
}

Write-Host "`n🏁 Мониторинг завершён" -ForegroundColor Cyan

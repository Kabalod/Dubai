# Railway Auto-Fix Script
# Автоматически мониторит логи и исправляет ошибки зависимостей

param(
    [string]$ServiceName = "workerproject-production"
)

Write-Host "🚀 Railway Auto-Fix Monitor запущен..." -ForegroundColor Green
Write-Host "Сервис: $ServiceName" -ForegroundColor Cyan

# Функция для получения логов
function Get-RailwayLogs {
    Write-Host "📋 Получение логов..." -ForegroundColor Yellow
    $logs = npx --yes @railway/cli@latest logs --service $ServiceName 2>&1
    return $logs -join "`n"
}

# Функция для обнаружения ошибок зависимостей
function Find-MissingDependencies {
    param([string]$LogText)
    
    $dependencies = @()
    
    # Паттерны для поиска недостающих модулей
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

# Функция для добавления зависимости в Dockerfile
function Add-DependencyToDockerfile {
    param([string]$Dependency)
    
    $dockerfilePath = "apps/realty-main/Dockerfile"
    
    if (!(Test-Path $dockerfilePath)) {
        Write-Host "❌ Dockerfile не найден: $dockerfilePath" -ForegroundColor Red
        return $false
    }
    
    $content = Get-Content $dockerfilePath -Raw
    
    # Найти последнюю строку с pip install
    $lastPipLine = ($content -split "`n" | Where-Object { $_ -match "pip install.*--no-cache-dir" })[-1]
    
    if ($lastPipLine) {
        # Добавить зависимость к последней строке pip install
        $newLine = $lastPipLine.TrimEnd() + " $Dependency"
        $content = $content -replace [regex]::Escape($lastPipLine), $newLine
        
        Set-Content $dockerfilePath $content -NoNewline
        Write-Host "✅ Добавлена зависимость: $Dependency" -ForegroundColor Green
        return $true
    }
    
    return $false
}

# Функция для коммита и пуша изменений
function Deploy-Fix {
    param([string[]]$Dependencies)
    
    $depList = $Dependencies -join ", "
    $commitMessage = "fix(deps): auto-add missing dependencies: $depList"
    
    Write-Host "📤 Коммит и пуш исправлений..." -ForegroundColor Yellow
    
    git add -A
    git commit -m $commitMessage
    git push
    
    Write-Host "✅ Исправления отправлены в Railway" -ForegroundColor Green
}

# Основной цикл мониторинга
$maxAttempts = 10
$attempt = 1

while ($attempt -le $maxAttempts) {
    Write-Host "`n🔍 Попытка $attempt из $maxAttempts" -ForegroundColor Cyan
    
    # Получить логи
    $logs = Get-RailwayLogs
    
    # Найти недостающие зависимости
    $missingDeps = Find-MissingDependencies -LogText $logs
    
    if ($missingDeps.Count -eq 0) {
        Write-Host "✅ Недостающих зависимостей не найдено!" -ForegroundColor Green
        
        # Проверить статус API
        try {
            $response = Invoke-RestMethod -Uri "https://workerproject-production.up.railway.app/api/health/" -Method GET -TimeoutSec 10
            Write-Host "🎉 Backend успешно запущен!" -ForegroundColor Green
            Write-Host "Ответ API: $($response | ConvertTo-Json)" -ForegroundColor Cyan
            break
        }
        catch {
            Write-Host "⚠️ API пока не отвечает, ждём..." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ Найдены недостающие зависимости:" -ForegroundColor Red
        $missingDeps | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        
        # Добавить зависимости в Dockerfile
        $added = @()
        foreach ($dep in $missingDeps) {
            if (Add-DependencyToDockerfile -Dependency $dep) {
                $added += $dep
            }
        }
        
        if ($added.Count -gt 0) {
            Deploy-Fix -Dependencies $added
            Write-Host "⏳ Ожидание пересборки (3 минуты)..." -ForegroundColor Yellow
            Start-Sleep -Seconds 180
        }
    }
    
    $attempt++
    Start-Sleep -Seconds 30
}

if ($attempt -gt $maxAttempts) {
    Write-Host "❌ Превышено максимальное количество попыток" -ForegroundColor Red
}

Write-Host "`n🏁 Railway Auto-Fix Monitor завершён" -ForegroundColor Green

# Real Estate Analytics Platform - PowerShell Script
# Автозапуск всех сервисов

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Real Estate Analytics Platform" -ForegroundColor Cyan
Write-Host "   Автозапуск всех сервисов" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Функция для запуска сервиса
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$Command,
        [string]$WorkingDirectory
    )
    
    Write-Host "[$ServiceName] Запуск..." -ForegroundColor Yellow
    
    if ($WorkingDirectory) {
        $fullPath = Join-Path $PSScriptRoot $WorkingDirectory
        if (Test-Path $fullPath) {
            Set-Location $fullPath
        } else {
            Write-Host "Ошибка: путь $fullPath не найден" -ForegroundColor Red
            return
        }
    }
    
    Start-Process -FilePath "cmd" -ArgumentList "/k", $Command -WindowStyle Normal
    Start-Sleep -Seconds 3
}

try {
    # 1. Property Analyzer (порт 8001)
    Write-Host "[1/4] Запуск Property Analyzer (порт 8001)..." -ForegroundColor Green
    Start-Service -ServiceName "Property Analyzer" -Command "venv\Scripts\python manage.py runserver 127.0.0.1:8001" -WorkingDirectory "pfimport-main"
    
    # 2. React Frontend (порт 5173)
    Write-Host "[2/4] Запуск React Frontend (порт 5173)..." -ForegroundColor Green
    Start-Service -ServiceName "React Frontend" -Command "npm run dev" -WorkingDirectory "DXB-frontend-develop"
    
    # 3. HTTP Server (порт 3000) - если не запущен
    Write-Host "[3/4] Проверка HTTP Server (порт 3000)..." -ForegroundColor Green
    $httpServer = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    if (-not $httpServer) {
        Write-Host "HTTP Server не запущен, запускаем..." -ForegroundColor Yellow
        Start-Service -ServiceName "HTTP Server" -Command "python -m http.server 3000"
    } else {
        Write-Host "HTTP Server уже запущен" -ForegroundColor Green
    }
    
    # 4. Проверка статуса
    Write-Host "[4/4] Проверка статуса..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Статус сервисов:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Проверяем Django Backend
    $djangoBackend = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($djangoBackend) {
        Write-Host "Django Backend:     http://localhost:8000 [ONLINE]" -ForegroundColor Green
    } else {
        Write-Host "Django Backend:     http://localhost:8000 [OFFLINE]" -ForegroundColor Red
    }
    
    # Проверяем Property Analyzer
    $propertyAnalyzer = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
    if ($propertyAnalyzer) {
        Write-Host "Property Analyzer:  http://localhost:8001 [ONLINE]" -ForegroundColor Green
    } else {
        Write-Host "Property Analyzer:  http://localhost:8001 [OFFLINE]" -ForegroundColor Red
    }
    
    # Проверяем React Frontend
    $reactFrontend = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
    if ($reactFrontend) {
        Write-Host "React Frontend:     http://localhost:5173 [ONLINE]" -ForegroundColor Green
    } else {
        Write-Host "React Frontend:     http://localhost:5173 [OFFLINE]" -ForegroundColor Red
    }
    
    # Проверяем HTTP Server
    $httpServer = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    if ($httpServer) {
        Write-Host "HTTP Server:        http://localhost:3000 [ONLINE]" -ForegroundColor Green
    } else {
        Write-Host "HTTP Server:        http://localhost:3000 [OFFLINE]" -ForegroundColor Red
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 Все сервисы запущены! Откройте дашборд:" -ForegroundColor Green
    Write-Host "http://localhost:3000/dashboard.html" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "Ошибка при запуске сервисов: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Нажмите любую клавишу для продолжения..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Проверка статуса email системы

Write-Host ""
Write-Host "📧 ПРОВЕРКА СТАТУСА EMAIL СИСТЕМЫ" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "🔍 1. Проверка файла .env:" -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "✅ Файл .env найден:" -ForegroundColor Green
    Write-Host "--------------------------------"
    Get-Content ".env"
    Write-Host "--------------------------------"
} else {
    Write-Host "❌ Файл .env не найден!" -ForegroundColor Red
    Write-Host "💡 Создайте .env с настройками SendGrid" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔍 2. Проверка контейнера:" -ForegroundColor Cyan
try {
    $containerStatus = docker compose ps realty-main-web --format json 2>$null | ConvertFrom-Json
    if ($containerStatus.State -eq "running") {
        Write-Host "✅ Контейнер realty-main-web запущен" -ForegroundColor Green
    } else {
        Write-Host "❌ Контейнер realty-main-web не запущен" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Не удается проверить статус контейнера" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔍 3. Последние логи email:" -ForegroundColor Cyan
docker compose logs realty-main-web --tail 10 | Select-String "📧|✅|❌|Email|SendGrid"

Write-Host ""
Write-Host "🧪 4. Тест API:" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -Method GET -TimeoutSec 5
    Write-Host "✅ API отвечает (статус: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ API не отвечает" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 СЛЕДУЮЩИЕ ШАГИ:" -ForegroundColor Yellow
Write-Host "=================="
Write-Host "1. Если нет .env файла → запустите: .\quick-setup-sendgrid.bat"
Write-Host "2. Если контейнер не запущен → запустите: docker compose --profile backend up -d"
Write-Host "3. Для полной инструкции → откройте: SENDGRID_ПОЛНАЯ_ИНСТРУКЦИЯ.md"
Write-Host ""

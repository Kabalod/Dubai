# Быстрая проверка статуса Railway backend
Write-Host "🔍 Проверка Railway backend..." -ForegroundColor Cyan

# Проверка API
try {
    $response = Invoke-RestMethod -Uri "https://workerproject-production.up.railway.app/api/health/" -Method GET -TimeoutSec 10
    Write-Host "✅ Backend работает!" -ForegroundColor Green
    Write-Host "Ответ: $($response | ConvertTo-Json)" -ForegroundColor White
}
catch {
    Write-Host "❌ Backend не отвечает" -ForegroundColor Red
    
    # Получить последние логи
    Write-Host "📋 Получение логов..." -ForegroundColor Yellow
    $logs = npx --yes @railway/cli@latest logs --service workerproject-production --tail 20 2>&1
    
    # Найти ошибки модулей
    $moduleErrors = $logs | Select-String "No module named|ModuleNotFoundError"
    
    if ($moduleErrors) {
        Write-Host "`n❌ Найдены ошибки модулей:" -ForegroundColor Red
        $moduleErrors | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    }
    
    # Показать последние строки логов
    Write-Host "`n📋 Последние логи:" -ForegroundColor Cyan
    $logs | Select-Object -Last 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
}

Write-Host "`n🎯 Для автоматического исправления запустите:" -ForegroundColor Green
Write-Host "  .\scripts\railway-auto-fix.ps1" -ForegroundColor Cyan

# Проверка статуса системы SendGrid и регистрации
Write-Host "🔍 Проверка статуса системы..." -ForegroundColor Green
Write-Host ""

# 1. Проверяем что бекенд запущен
Write-Host "1️⃣ Проверяем доступность бекенда..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri 'http://localhost:8000/api/health/' -Method GET
    $healthData = $healthResponse.Content | ConvertFrom-Json
    
    Write-Host "✅ Бекенд доступен" -ForegroundColor Green
    Write-Host "📧 Email Backend: $($healthData.email_backend)" -ForegroundColor Cyan
    Write-Host "🔧 SendGrid настроен: $($healthData.sendgrid_configured)" -ForegroundColor Cyan
    
    if ($healthData.sendgrid_configured -eq $true) {
        Write-Host "🎉 SendGrid ГОТОВ к отправке реальных email!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ SendGrid НЕ настроен - будет использоваться fallback" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Бекенд недоступен на http://localhost:8000" -ForegroundColor Red
    Write-Host "💡 Запустите: docker compose --profile backend up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. Проверяем Docker контейнеры
Write-Host "2️⃣ Проверяем Docker контейнеры..." -ForegroundColor Yellow
try {
    $containers = docker ps --filter "name=realty-main-web" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка проверки Docker контейнеров" -ForegroundColor Red
}

Write-Host ""

# 3. Показываем логи
Write-Host "3️⃣ Последние логи бекенда..." -ForegroundColor Yellow
try {
    docker compose logs realty-main-web --tail 5
} catch {
    Write-Host "❌ Ошибка получения логов" -ForegroundColor Red
}

Write-Host ""
Write-Host "📝 Для тестирования регистрации запустите:" -ForegroundColor Blue
Write-Host "   .\test-registration.ps1 -Email your-email@gmail.com" -ForegroundColor Cyan
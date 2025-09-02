# Railway Health Check - комплексная проверка деплоя
# Проверяет статус сервисов, переменные окружения и логи

Write-Host "🚂 RAILWAY HEALTH CHECK" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# 1. ПРОВЕРКА ПОДКЛЮЧЕНИЯ К RAILWAY
Write-Host "`n🔗 Проверка подключения к Railway..." -ForegroundColor Cyan

try {
    $status = npx --yes @railway/cli@latest status --json 2>&1 | ConvertFrom-Json
    Write-Host "✅ Подключен к проекту: $($status.name)" -ForegroundColor Green
    Write-Host "   ID: $($status.id)" -ForegroundColor White
} catch {
    Write-Host "❌ Не удалось подключиться к Railway" -ForegroundColor Red
    Write-Host "   Выполните: railway link" -ForegroundColor Yellow
    exit 1
}

# 2. ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
Write-Host "`n⚙️ Проверка переменных окружения..." -ForegroundColor Cyan

$requiredVars = @(
    "DATABASE_URL",
    "DEBUG", 
    "DJANGO_ALLOWED_HOSTS",
    "SECRET_KEY",
    "SENDGRID_API_KEY",
    "DEFAULT_FROM_EMAIL"
)

Write-Host "Требуемые переменные:" -ForegroundColor White
foreach ($var in $requiredVars) {
    Write-Host "  - $var" -ForegroundColor Yellow
}

# 3. ПРОВЕРКА СТАТУСА СЕРВИСОВ
Write-Host "`n🏃 Проверка статуса сервисов..." -ForegroundColor Cyan

# Backend API
Write-Host "Backend API:" -ForegroundColor White
try {
    $response = Invoke-RestMethod -Uri "https://workerproject-production.up.railway.app/api/health/" -Method GET -TimeoutSec 10
    Write-Host "✅ Backend отвечает" -ForegroundColor Green
    Write-Host "   Статус: $($response.status)" -ForegroundColor White
    Write-Host "   Сервис: $($response.service)" -ForegroundColor White
    if ($response.message) {
        Write-Host "   Сообщение: $($response.message)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Backend не отвечает" -ForegroundColor Red
    Write-Host "   Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    
    # Получаем логи для диагностики
    Write-Host "`n📋 Получение логов для диагностики..." -ForegroundColor Yellow
    try {
        $logs = npx --yes @railway/cli@latest logs --json 2>&1
        if ($logs -match "No deployments found") {
            Write-Host "⚠️ Деплойменты не найдены - возможно, сборка ещё не завершена" -ForegroundColor Yellow
        } else {
            Write-Host "Последние логи:" -ForegroundColor White
            $logs | Select-Object -Last 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    } catch {
        Write-Host "❌ Не удалось получить логи" -ForegroundColor Red
    }
}

# Frontend
Write-Host "`nFrontend:" -ForegroundColor White
try {
    $frontendResponse = Invoke-WebRequest -Uri "https://frontend-production-fa38.up.railway.app/" -Method GET -TimeoutSec 10
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend доступен" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend недоступен" -ForegroundColor Red
    Write-Host "   Ошибка: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. ПРОВЕРКА OTP ENDPOINTS
Write-Host "`n📧 Проверка OTP endpoints..." -ForegroundColor Cyan

$otpEndpoints = @(
    "https://workerproject-production.up.railway.app/api/auth/send-otp/",
    "https://workerproject-production.up.railway.app/api/auth/verify-otp/"
)

foreach ($endpoint in $otpEndpoints) {
    try {
        # Проверяем только доступность endpoint (OPTIONS запрос)
        $response = Invoke-WebRequest -Uri $endpoint -Method OPTIONS -TimeoutSec 5
        Write-Host "✅ $endpoint доступен" -ForegroundColor Green
    } catch {
        if ($_.Exception.Response.StatusCode -eq 405) {
            Write-Host "✅ $endpoint доступен (405 Method Not Allowed - нормально для OPTIONS)" -ForegroundColor Green
        } else {
            Write-Host "❌ $endpoint недоступен" -ForegroundColor Red
        }
    }
}

# 5. РЕКОМЕНДАЦИИ
Write-Host "`n💡 РЕКОМЕНДАЦИИ:" -ForegroundColor Cyan

Write-Host "Для тестирования OTP системы:" -ForegroundColor White
Write-Host "1. Откройте: https://frontend-production-fa38.up.railway.app/auth" -ForegroundColor Yellow
Write-Host "2. Введите email: kbalodk@gmail.com" -ForegroundColor Yellow
Write-Host "3. Нажмите 'SIGN UP'" -ForegroundColor Yellow
Write-Host "4. Проверьте почту на код от SendGrid" -ForegroundColor Yellow

Write-Host "`nДля мониторинга:" -ForegroundColor White
Write-Host "- Логи: npx @railway/cli@latest logs" -ForegroundColor Yellow
Write-Host "- Статус: npx @railway/cli@latest status" -ForegroundColor Yellow
Write-Host "- Деплой: npx @railway/cli@latest up" -ForegroundColor Yellow

Write-Host "`n🏁 Railway Health Check завершён!" -ForegroundColor Green

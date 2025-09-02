Write-Host "🧪 Финальный тест reg.ru SMTP" -ForegroundColor Green
Write-Host "📧 Сервер: sm12.hosting.reg.ru:587" -ForegroundColor Cyan
Write-Host ""

# Простой тест
$headers = @{'Content-Type' = 'application/json'}
$testEmail = Read-Host "Введите ваш email для тестирования"

$body = @{
    email = $testEmail
    first_name = "Test"
    last_name = "RegRu"
} | ConvertTo-Json

Write-Host "📤 Отправляем запрос..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "📋 Результат:" -ForegroundColor Blue
    Write-Host "  Email отправлен: $($data.email_sent)" -ForegroundColor $(if($data.email_sent) {'Green'} else {'Red'})
    Write-Host "  OTP код: $($data.otp_code)" -ForegroundColor Yellow
    
    if ($data.email_error) {
        Write-Host "  Ошибка: $($data.email_error)" -ForegroundColor Red
    }
    
    if ($data.email_sent) {
        Write-Host ""
        Write-Host "🎉 УСПЕХ! Проверьте почту $testEmail" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📜 Проверяем последние логи:" -ForegroundColor Blue
docker compose logs realty-main-web --tail 5

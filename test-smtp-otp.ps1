# Тест отправки OTP через SendGrid SMTP Relay
param(
    [Parameter(Mandatory=$false)]
    [string]$Email = "test-otp@example.com"
)

Write-Host "🧪 Тестирование отправки OTP через SendGrid SMTP Relay" -ForegroundColor Green
Write-Host "📧 Email: $Email" -ForegroundColor Cyan
Write-Host ""

# Подготавливаем данные
$headers = @{
    'Content-Type' = 'application/json'
}

$body = @{
    email = $Email
    first_name = "SMTP"
    last_name = "Test"
} | ConvertTo-Json

Write-Host "📤 Отправляем запрос на регистрацию..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body
    $responseData = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Ответ получен!" -ForegroundColor Green
    Write-Host "📧 Email sent: $($responseData.email_sent)" -ForegroundColor Cyan
    Write-Host "⏰ Expires in: $($responseData.expires_in) секунд" -ForegroundColor Cyan
    
    if ($responseData.otp_code) {
        Write-Host "🔑 OTP код: $($responseData.otp_code)" -ForegroundColor Yellow
    }
    
    if ($responseData.email_error) {
        Write-Host "❌ Email ошибка: $($responseData.email_error)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "📬 Проверьте почту $Email" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Ошибка запроса:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "📄 Детали ошибки: $errorContent" -ForegroundColor Yellow
    }
}

# Проверяем логи
Write-Host ""
Write-Host "📜 Последние логи сервера:" -ForegroundColor Blue
docker compose logs realty-main-web --tail 5

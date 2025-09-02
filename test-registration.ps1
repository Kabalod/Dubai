# Тестирование полного цикла регистрации с SendGrid
# Замените email на ваш реальный для тестирования

param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    [string]$FirstName = "Test",
    [string]$LastName = "User"
)

Write-Host "🧪 Тестирование регистрации для: $Email" -ForegroundColor Green
Write-Host ""

# 1. Регистрация пользователя
Write-Host "1️⃣ Отправляем запрос на регистрацию..." -ForegroundColor Yellow
$headers = @{'Content-Type' = 'application/json'}
$body = @{
    email = $Email
    first_name = $FirstName
    last_name = $LastName
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body
    $responseData = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Регистрация успешна!" -ForegroundColor Green
    Write-Host "📧 Email отправлен: $($responseData.email_sent)" -ForegroundColor Cyan
    Write-Host "⏰ Срок действия: $($responseData.expires_in) секунд" -ForegroundColor Cyan
    
    if ($responseData.otp_code) {
        Write-Host "🔑 OTP код (для тестирования): $($responseData.otp_code)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "📬 Проверьте свою почту $Email на наличие письма с кодом подтверждения" -ForegroundColor Green
    Write-Host ""
    
    # 2. Ждем ввода OTP кода
    $otpCode = Read-Host "Введите OTP код из письма"
    
    if ($otpCode) {
        Write-Host ""
        Write-Host "2️⃣ Проверяем OTP код..." -ForegroundColor Yellow
        
        $verifyBody = @{
            email = $Email
            code = $otpCode
            first_name = $FirstName
            last_name = $LastName
        } | ConvertTo-Json
        
        try {
            $verifyResponse = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/verify-otp/' -Method POST -Headers $headers -Body $verifyBody
            $verifyData = $verifyResponse.Content | ConvertFrom-Json
            
            Write-Host "✅ OTP код подтвержден!" -ForegroundColor Green
            Write-Host "🎉 Пользователь создан: $($verifyData.user.email)" -ForegroundColor Green
            Write-Host "🔐 Access Token: $($verifyData.access.Substring(0, 20))..." -ForegroundColor Cyan
            Write-Host ""
            Write-Host "🎊 РЕГИСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!" -ForegroundColor Green
            
        } catch {
            $errorResponse = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorResponse)
            $errorData = $reader.ReadToEnd() | ConvertFrom-Json
            Write-Host "❌ Ошибка проверки OTP: $($errorData.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ OTP код не введен" -ForegroundColor Red
    }
    
} catch {
    $errorResponse = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($errorResponse)
    $errorData = $reader.ReadToEnd() | ConvertFrom-Json
    Write-Host "❌ Ошибка регистрации: $($errorData.error)" -ForegroundColor Red
    if ($errorData.suggestion) {
        Write-Host "💡 Совет: $($errorData.suggestion)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🏁 Тестирование завершено" -ForegroundColor Blue

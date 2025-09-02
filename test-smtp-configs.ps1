# Тестирование разных SMTP конфигураций для reg.ru
Write-Host "🔧 Тестирование SMTP конфигураций reg.ru..." -ForegroundColor Green
Write-Host ""

# Массив конфигураций для тестирования
$configs = @(
    @{name="REG.RU Standard"; host="smtp.reg.ru"; port=587; tls=$true; ssl=$false},
    @{name="REG.RU SSL"; host="smtp.reg.ru"; port=465; tls=$false; ssl=$true},
    @{name="Domain SMTP"; host="mail.kabalod.online"; port=587; tls=$true; ssl=$false},
    @{name="Domain Plain"; host="mail.kabalod.online"; port=25; tls=$false; ssl=$false}
)

foreach ($config in $configs) {
    Write-Host "📧 Тестируем: $($config.name)" -ForegroundColor Yellow
    Write-Host "   Сервер: $($config.host):$($config.port)" -ForegroundColor Cyan
    Write-Host "   TLS: $($config.tls), SSL: $($config.ssl)" -ForegroundColor Cyan
    
    # Обновляем docker-compose.yml
    (Get-Content docker-compose.yml) | ForEach-Object {
        $_ -replace 'EMAIL_HOST=.*', "EMAIL_HOST=$($config.host)" `
           -replace 'EMAIL_PORT=.*', "EMAIL_PORT=$($config.port)" `
           -replace 'EMAIL_USE_TLS=.*', "EMAIL_USE_TLS=$($config.tls)" `
           -replace 'EMAIL_USE_SSL=.*', "EMAIL_USE_SSL=$($config.ssl)"
    } | Set-Content docker-compose.yml
    
    # Перезапускаем контейнер
    Write-Host "   🔄 Перезапуск..." -ForegroundColor Gray
    docker compose restart realty-main-web | Out-Null
    Start-Sleep 3
    
    # Тестируем отправку
    try {
        $headers = @{'Content-Type' = 'application/json'}
        $body = @{
            email = "test-$($config.name.Replace(' ', '').ToLower())@gmail.com"
            first_name = "Test"
            last_name = $config.name
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body -TimeoutSec 10
        $responseData = $response.Content | ConvertFrom-Json
        
        if ($responseData.email_sent -eq $true) {
            Write-Host "   ✅ УСПЕХ! Email отправлен" -ForegroundColor Green
            Write-Host "   🎉 Используйте эту конфигурацию!" -ForegroundColor Green
            break
        } else {
            Write-Host "   ❌ Не удалось отправить" -ForegroundColor Red
            if ($responseData.email_error) {
                Write-Host "   💬 Ошибка: $($responseData.email_error)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "   ❌ Ошибка запроса: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "🏁 Тестирование завершено" -ForegroundColor Blue

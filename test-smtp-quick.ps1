# Быстрое тестирование SMTP настроек reg.ru
Write-Host "🔧 Быстрое тестирование SMTP настроек reg.ru" -ForegroundColor Green

$configs = @(
    @{host="mail.kabalod.online"; port=25; tls=$false; ssl=$false; name="Mail KabalodOnline Port 25"},
    @{host="mail.kabalod.online"; port=465; tls=$false; ssl=$true; name="Mail KabalodOnline Port 465"},
    @{host="smtp.kabalod.online"; port=587; tls=$true; ssl=$false; name="SMTP KabalodOnline Port 587"},
    @{host="smtp.kabalod.online"; port=465; tls=$false; ssl=$true; name="SMTP KabalodOnline Port 465"}
)

foreach ($config in $configs) {
    Write-Host "📧 Тестируем: $($config.name)" -ForegroundColor Yellow
    
    # Обновляем docker-compose.yml
    $content = Get-Content docker-compose.yml -Raw
    $content = $content -replace 'EMAIL_HOST=.*', "EMAIL_HOST=$($config.host)"
    $content = $content -replace 'EMAIL_PORT=.*', "EMAIL_PORT=$($config.port)"
    $content = $content -replace 'EMAIL_USE_TLS=.*', "EMAIL_USE_TLS=$($config.tls)"
    $content = $content -replace 'EMAIL_USE_SSL=.*', "EMAIL_USE_SSL=$($config.ssl)"
    Set-Content docker-compose.yml $content
    
    # Перезапускаем
    Write-Host "   🔄 Перезапуск..." -ForegroundColor Gray
    docker compose restart realty-main-web | Out-Null
    Start-Sleep 3
    
    # Тестируем
    try {
        $testEmail = "test.$($config.host.Replace('.',''))$($config.port)@gmail.com"
        $body = @{
            email = $testEmail
            first_name = "Test"
            last_name = $config.name
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers @{'Content-Type'='application/json'} -Body $body -TimeoutSec 10
        $data = $response.Content | ConvertFrom-Json
        
        if ($data.email_sent -eq $true) {
            Write-Host "   ✅ РАБОТАЕТ! Email отправлен" -ForegroundColor Green
            Write-Host "   🎉 Используйте эти настройки!" -ForegroundColor Green
            Write-Host "   Host: $($config.host), Port: $($config.port), TLS: $($config.tls), SSL: $($config.ssl)" -ForegroundColor Cyan
            break
        } else {
            Write-Host "   ❌ Не работает: $($data.email_error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "🏁 Тестирование завершено" -ForegroundColor Blue

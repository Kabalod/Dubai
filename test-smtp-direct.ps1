# Тест SMTP подключения напрямую с хоста
Write-Host "🔧 Тестирование SMTP подключения с хоста к reg.ru" -ForegroundColor Green

# Тестируем доступность портов
$hosts = @("mail.kabalod.online", "31.31.196.114")
$ports = @(25, 587, 465)

foreach ($host in $hosts) {
    foreach ($port in $ports) {
        Write-Host "📡 Тестируем $host:$port" -ForegroundColor Yellow
        
        try {
            $connection = Test-NetConnection -ComputerName $host -Port $port -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                Write-Host "   ✅ $host:$port доступен" -ForegroundColor Green
            } else {
                Write-Host "   ❌ $host:$port недоступен" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

Write-Host "🏁 Тестирование завершено" -ForegroundColor Blue

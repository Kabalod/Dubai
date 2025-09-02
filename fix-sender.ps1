# Скрипт для быстрого исправления проблемы с отправителем
param(
    [Parameter(Mandatory=$true)]
    [string]$YourEmail
)

Write-Host "🔧 Обновляем настройки для использования $YourEmail как отправитель..." -ForegroundColor Yellow

# Обновляем docker-compose.yml
$dockerCompose = Get-Content docker-compose.yml -Raw
$dockerCompose = $dockerCompose -replace 'DEFAULT_FROM_EMAIL=noreply@kabalod.online', "DEFAULT_FROM_EMAIL=$YourEmail"

Set-Content -Path docker-compose.yml -Value $dockerCompose

Write-Host "✅ docker-compose.yml обновлен" -ForegroundColor Green

# Перезапускаем бекенд
Write-Host "🔄 Перезапускаем бекенд..." -ForegroundColor Yellow
docker compose restart realty-main-web

Write-Host "✅ Готово! Теперь письма будут отправляться от: $YourEmail" -ForegroundColor Green
Write-Host "📧 Проверьте что $YourEmail верифицирован в SendGrid" -ForegroundColor Cyan

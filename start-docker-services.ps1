Write-Host "Starting all services via Docker Compose..." -ForegroundColor Green
Write-Host ""

Write-Host "Starting Django Backend (realty-main)..." -ForegroundColor Yellow
Set-Location "realty-main"
docker compose --profile local up --build -d
Write-Host "Django Backend started on http://localhost:8000" -ForegroundColor Green
Write-Host ""

Write-Host "Starting React Frontend (DXB-frontend-develop)..." -ForegroundColor Yellow
Set-Location "..\DXB-frontend-develop"
docker compose up --build -d
Write-Host "React Frontend started on http://localhost:3000" -ForegroundColor Green
Write-Host ""

Write-Host "Starting pfimport-main..." -ForegroundColor Yellow
Set-Location "..\pfimport-main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python manage.py runserver 8002"
Write-Host "pfimport-main started on http://localhost:8002" -ForegroundColor Green
Write-Host ""

Write-Host "All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Django Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "pfimport: http://localhost:8002" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

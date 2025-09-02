# Local Development Startup Script for Dubai MVP
# This script starts the project locally using Docker

Write-Host "🚀 Starting Dubai MVP Local Development Environment..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml down --remove-orphans

# Remove old images (optional)
$cleanImages = Read-Host "🧹 Clean old Docker images? (y/n)"
if ($cleanImages -eq "y" -or $cleanImages -eq "Y") {
    Write-Host "🧹 Cleaning old images..." -ForegroundColor Yellow
    docker system prune -f
}

# Build and start services
Write-Host "🔨 Building and starting services..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml up --build -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml ps

# Show logs
Write-Host "📋 Showing recent logs..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml logs --tail=20

Write-Host ""
Write-Host "🎉 Local development environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Services available at:" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White

Write-Host "   • Django Admin: http://localhost:8000/admin/" -ForegroundColor White
Write-Host "   • Health Check: http://localhost:8000/health/" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "   • View logs: docker-compose -f docker-compose.local.yml logs -f" -ForegroundColor White
Write-Host "   • Stop services: docker-compose -f docker-compose.local.yml down" -ForegroundColor White
Write-Host "   • Restart services: docker-compose -f docker-compose.local.yml restart" -ForegroundColor White
Write-Host "   • Access Django shell: docker exec -it dubai-django-local python manage.py shell" -ForegroundColor White
Write-Host ""

# Direct access (nginx removed):
Write-Host "🌐 Services available at:" -ForegroundColor Yellow
Write-Host "   • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White

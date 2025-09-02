# Stop Local Development Environment Script for Dubai MVP
# This script stops all local Docker services

Write-Host "🛑 Stopping Dubai MVP Local Development Environment..." -ForegroundColor Yellow

# Stop and remove containers
Write-Host "🔄 Stopping containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml down --remove-orphans

# Remove volumes (optional)
$removeVolumes = Read-Host "🗑️ Remove volumes (database data will be lost)? (y/n)"
if ($removeVolumes -eq "y" -or $removeVolumes -eq "Y") {
    Write-Host "🗑️ Removing volumes..." -ForegroundColor Yellow
    docker-compose -f docker-compose.local.yml down -v
    Write-Host "✅ Volumes removed" -ForegroundColor Green
}

# Clean up unused Docker resources (optional)
$cleanup = Read-Host "🧹 Clean up unused Docker resources? (y/n)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    docker system prune -f
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Local development environment stopped successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 To start again, run: .\start-local.ps1" -ForegroundColor Cyan

# Railway Deployment Script for Dubai MVP
# This script deploys the project to Railway

Write-Host "🚀 Deploying Dubai MVP to Railway..." -ForegroundColor Green

# Check if Railway CLI is installed
try {
    $railwayVersion = railway --version
    Write-Host "✅ Railway CLI is installed: $railwayVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI is not installed. Installing..." -ForegroundColor Yellow
    Write-Host "Please install Railway CLI from: https://railway.app/cli" -ForegroundColor Red
    exit 1
}

# Check if user is logged in
try {
    $userInfo = railway whoami
    Write-Host "✅ Logged in as: $userInfo" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Railway. Please login first:" -ForegroundColor Red
    Write-Host "railway login" -ForegroundColor Yellow
    exit 1
}

# Show current project status
Write-Host "📊 Current project status:" -ForegroundColor Yellow
railway status

# Ask for confirmation
$confirm = Read-Host "🚀 Proceed with deployment to Railway? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 0
}

# Build and deploy
Write-Host "🔨 Building and deploying..." -ForegroundColor Yellow
railway up

# Check deployment status
Write-Host "📋 Checking deployment status..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
railway status

# Show logs
Write-Host "📋 Recent logs:" -ForegroundColor Yellow
railway logs --tail=20

Write-Host ""
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Useful Railway commands:" -ForegroundColor Cyan
Write-Host "   • View logs: railway logs -f" -ForegroundColor White
Write-Host "   • Check status: railway status" -ForegroundColor White
Write-Host "   • Open in browser: railway open" -ForegroundColor White
Write-Host "   • View variables: railway variables" -ForegroundColor White
Write-Host "   • Connect to shell: railway shell" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Your app should be available at the Railway URL above" -ForegroundColor Green

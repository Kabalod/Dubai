# Manual Railway Deployment Script for Dubai MVP
# This script deploys the project to Railway manually

Write-Host "🚀 Manual Railway Deployment for Dubai MVP..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "railway.json")) {
    Write-Host "❌ railway.json not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Check if we have the required files
$requiredFiles = @("Dockerfile.railway", "requirements.txt", "manage.py", "realty/")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file/directory not found: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Check if Railway CLI is available
try {
    $railwayVersion = npx @railway/cli --version
    Write-Host "✅ Railway CLI available: $railwayVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI not available. Installing..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Check if user is logged in
Write-Host "🔐 Checking Railway login status..." -ForegroundColor Yellow
try {
    $loginStatus = npx @railway/cli whoami
    Write-Host "✅ Logged in as: $loginStatus" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Railway. Please login first:" -ForegroundColor Red
    Write-Host "npx @railway/cli login" -ForegroundColor Yellow
    exit 1
}

# Show current project status
Write-Host "📊 Current Railway project status:" -ForegroundColor Yellow
npx @railway/cli status

# Ask for confirmation
$confirm = Read-Host "🚀 Proceed with deployment to Railway? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 0
}

# Build and deploy
Write-Host "🔨 Building and deploying..." -ForegroundColor Yellow
npx @railway/cli up

# Check deployment status
Write-Host "📋 Checking deployment status..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
npx @railway/cli status

# Show logs
Write-Host "📋 Recent logs:" -ForegroundColor Yellow
npx @railway/cli logs --tail=20

Write-Host ""
Write-Host "🎉 Manual deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Useful Railway commands:" -ForegroundColor Cyan
Write-Host "   • View logs: npx @railway/cli logs -f" -ForegroundColor White
Write-Host "   • Check status: npx @railway/cli status" -ForegroundColor White
Write-Host "   • Open in browser: npx @railway/cli open" -ForegroundColor White
Write-Host "   • View variables: npx @railway/cli variables" -ForegroundColor White
Write-Host "   • Connect to shell: npx @railway/cli shell" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Your app should be available at the Railway URL above" -ForegroundColor Green

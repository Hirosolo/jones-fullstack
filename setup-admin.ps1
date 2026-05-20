# Admin Panel Setup Script for Docker
# Run this script from the deploy/hetzner directory

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Jones Shop Admin Panel Setup" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$currentLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
$hetznerDir = Join-Path $currentLocation "deploy\hetzner"

# Check if we're in the right directory
if (-not (Test-Path "$hetznerDir\docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml not found in $hetznerDir" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Change to hetzner directory
Set-Location $hetznerDir
Write-Host "[1/3] Ensuring Docker containers are running..." -ForegroundColor Yellow

# Start containers
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start Docker containers" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] ✓ Docker containers started`n" -ForegroundColor Green

# Wait for database to be ready
Write-Host "[2/3] Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Run migrations
docker compose exec -T api python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Migration command returned error" -ForegroundColor Yellow
}

Write-Host "[2/3] ✓ Database ready`n" -ForegroundColor Green

# Create admin account
Write-Host "[3/3] Creating default admin account..." -ForegroundColor Yellow
docker compose exec -T api python manage.py create_default_admin
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create admin account" -ForegroundColor Red
    exit 1
}

Write-Host "`n================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Green

Write-Host "Admin Panel URL:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/admin/login/" -ForegroundColor White

Write-Host "`nCredentials:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: t123" -ForegroundColor White

Write-Host "`nAvailable Routes:" -ForegroundColor Cyan
Write-Host "  Dashboard:  http://localhost:8000/admin/dashboard/" -ForegroundColor White
Write-Host "  Products:   http://localhost:8000/admin/products/" -ForegroundColor White
Write-Host "  Articles:   http://localhost:8000/admin/articles/" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Open your browser to http://localhost:8000/admin/login/" -ForegroundColor White
Write-Host "  2. Login with username: admin, password: t123" -ForegroundColor White
Write-Host "  3. Start managing your products and articles!" -ForegroundColor White

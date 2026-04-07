$ErrorActionPreference = "Stop"

Write-Host "========== LH Contract Management System - Dev Setup ==========" -ForegroundColor Cyan

# 1. Check Docker Database
Write-Host "`n[1/3] Checking Database..." -ForegroundColor Yellow
$containerName = "lh_contract_db"
if (!(docker ps -q -f name=$containerName)) {
    Write-Host "Database container '$containerName' is NOT running. Starting..." -ForegroundColor Yellow
    docker-compose up -d db
    Write-Host "Waiting for Database to be ready..."
    Start-Sleep -Seconds 10
} else {
    Write-Host "Database is running." -ForegroundColor Green
}

# 2. Validate Backend Environment
Write-Host "`n[2/3] Validating Backend Environment..." -ForegroundColor Yellow
$pythonPath = ".\backend\venv_win\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "Python environment found at $pythonPath" -ForegroundColor Green
} else {
    Write-Host "Python environment not found at $pythonPath" -ForegroundColor Red
    exit 1
}

# 3. Start Backend
Write-Host "`n[3/3] Starting Backend..." -ForegroundColor Yellow
$backendPath = ".\backend"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; ..\backend\venv_win\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "Backend started in new window (Port 8000)." -ForegroundColor Green

# 4. Start Frontend
Write-Host "`nStarting Frontend..." -ForegroundColor Yellow
$frontendPath = ".\frontend"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
Write-Host "Frontend started in new window." -ForegroundColor Green

Write-Host "`n========== Setup Complete! ==========" -ForegroundColor Cyan
Write-Host "Access the app at: http://localhost:3000" -ForegroundColor Cyan

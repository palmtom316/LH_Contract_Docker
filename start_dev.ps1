$ErrorActionPreference = "Stop"

Write-Host "========== LH Contract Management System - Dev Setup ==========" -ForegroundColor Cyan

# 1. Check Docker Database
Write-Host "`n[1/4] Checking Database..." -ForegroundColor Yellow
$containerName = "lh_contract_db"
if (!(docker ps -q -f name=$containerName)) {
    Write-Host "Database container '$containerName' is NOT running. Starting..." -ForegroundColor Yellow
    docker-compose up -d db
    Write-Host "Waiting for Database to be ready..."
    Start-Sleep -Seconds 10
} else {
    Write-Host "Database is running." -ForegroundColor Green
}

# 2. Reset and Populate Test Data
Write-Host "`n[2/4] Resetting and Populating Test Data..." -ForegroundColor Yellow
$pythonPath = ".\backend\venv_win\Scripts\python.exe"
if (Test-Path $pythonPath) {
    & $pythonPath populate_test_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Test data populated successfully." -ForegroundColor Green
    } else {
        Write-Host "Failed to populate test data. Please check logs." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Python environment not found at $pythonPath" -ForegroundColor Red
    exit 1
}

# 3. Start Backend
Write-Host "`n[3/4] Starting Backend..." -ForegroundColor Yellow
$backendPath = ".\backend"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; ..\backend\venv_win\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "Backend started in new window (Port 8000)." -ForegroundColor Green

# 4. Start Frontend
Write-Host "`n[4/4] Starting Frontend..." -ForegroundColor Yellow
$frontendPath = ".\frontend"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
Write-Host "Frontend started in new window." -ForegroundColor Green

Write-Host "`n========== Setup Complete! ==========" -ForegroundColor Cyan
Write-Host "Access the app at: http://localhost:5173" -ForegroundColor Cyan

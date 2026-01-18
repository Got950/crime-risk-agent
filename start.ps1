# SPADE Risk Assessment Agent - Quick Start Script
# Paste this entire script into PowerShell to start both backend and frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SPADE Risk Assessment Agent" -ForegroundColor White
Write-Host "  Starting Backend and Frontend..." -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop existing processes
Write-Host "[1/4] Stopping existing processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*node*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

# Start Backend
Write-Host "[2/4] Starting Backend..." -ForegroundColor Green
$backendPath = Join-Path $PSScriptRoot "spade-risk-agent"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; py -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload" -WindowStyle Normal
Start-Sleep -Seconds 5

# Check and install frontend dependencies
Write-Host "[3/4] Checking Frontend..." -ForegroundColor Green
$frontendPath = Join-Path $PSScriptRoot "frontend"
if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    Write-Host "  Installing dependencies (first time only)..." -ForegroundColor Yellow
    Set-Location $frontendPath
    npm install
    Set-Location $PSScriptRoot
}

# Start Frontend
Write-Host "[4/4] Starting Frontend..." -ForegroundColor Green
$env:BROWSER = "default"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; `$env:BROWSER='default'; npm start" -WindowStyle Normal

# Wait for frontend and open browser
Write-Host ""
Write-Host "Waiting for frontend to compile..." -ForegroundColor Cyan
$maxWait = 60
$waited = 0
$frontendRunning = $false

while ($waited -lt $maxWait -and -not $frontendRunning) {
    Start-Sleep -Seconds 5
    $waited += 5
    $conn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    if ($conn) {
        $frontendRunning = $true
        Write-Host "✅ Frontend is running!" -ForegroundColor Green
    } else {
        Write-Host "   Still compiling... ($waited seconds)" -ForegroundColor Gray
    }
}

# Open browser
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Project Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Browser should be open now!" -ForegroundColor Green
Write-Host "Two PowerShell windows are running the servers." -ForegroundColor Gray





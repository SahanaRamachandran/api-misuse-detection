# ============================================================================
# Real-time Anomaly Detection - Quick Start Script
# ============================================================================
# This script helps you set up and test the real-time detection system
# Author: Traffic Monitoring System
# Date: February 2026
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "Real-time Anomaly Detection - Quick Start" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================
Write-Host "[Step 1/5] Checking Prerequisites..." -ForegroundColor Yellow

# Check Python
Write-Host "  • Checking Python..." -ForegroundColor Gray
try {
    $pythonVersion = python --version 2>&1
    Write-Host "    ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "    ✗ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if in backend/security directory
$currentDir = Get-Location
if (-not ($currentDir -match "backend\\security$")) {
    Write-Host "  ⚠ Not in backend\security directory" -ForegroundColor Yellow
    Write-Host "  Changing directory..." -ForegroundColor Gray
    
    # Try to find the security directory
    if (Test-Path "backend\security") {
        cd backend\security
        Write-Host "    ✓ Changed to backend\security" -ForegroundColor Green
    } elseif (Test-Path "..\..\backend\security") {
        cd ..\..\backend\security
        Write-Host "    ✓ Changed to backend\security" -ForegroundColor Green
    } else {
        Write-Host "    ✗ Cannot find backend\security directory!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✓ Prerequisites check complete`n" -ForegroundColor Green

# ============================================================================
# Step 2: Check Models Directory
# ============================================================================
Write-Host "[Step 2/5] Checking ML Models..." -ForegroundColor Yellow

$modelsDir = "..\models"
$requiredModels = @("xgb_model.pkl", "tfidf.pkl", "autoencoder.h5", "scaler.pkl")
$missingModels = @()

foreach ($model in $requiredModels) {
    $modelPath = Join-Path $modelsDir $model
    if (Test-Path $modelPath) {
        Write-Host "  ✓ Found: $model" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing: $model" -ForegroundColor Red
        $missingModels += $model
    }
}

if ($missingModels.Count -gt 0) {
    Write-Host "`n  ⚠ WARNING: Some models are missing!" -ForegroundColor Yellow
    Write-Host "  The system will run in 'fail-open' mode (no ML detection)" -ForegroundColor Yellow
    Write-Host "`n  Missing models:" -ForegroundColor Yellow
    foreach ($model in $missingModels) {
        Write-Host "    - $model" -ForegroundColor Gray
    }
    Write-Host "`n  To enable full detection, place trained models in: $modelsDir" -ForegroundColor Gray
} else {
    Write-Host "`n✓ All models found`n" -ForegroundColor Green
}

# ============================================================================
# Step 3: Check Dependencies
# ============================================================================
Write-Host "[Step 3/5] Checking Python Dependencies..." -ForegroundColor Yellow

$requiredPackages = @(
    "fastapi",
    "uvicorn",
    "tensorflow",
    "xgboost",
    "scikit-learn",
    "numpy",
    "joblib"
)

$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $result = python -c "import $package; print('OK')" 2>&1
        if ($result -match "OK") {
            Write-Host "  ✓ $package" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $package (not found)" -ForegroundColor Red
            $missingPackages += $package
        }
    } catch {
        Write-Host "  ✗ $package (not found)" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "`n  ⚠ Some packages are missing!" -ForegroundColor Yellow
    Write-Host "  Installing missing packages..." -ForegroundColor Gray
    
    foreach ($package in $missingPackages) {
        Write-Host "    Installing $package..." -ForegroundColor Gray
        pip install $package
    }
    
    Write-Host "`n  ✓ Installation complete" -ForegroundColor Green
} else {
    Write-Host "`n✓ All dependencies installed`n" -ForegroundColor Green
}

# ============================================================================
# Step 4: Start the API
# ============================================================================
Write-Host "[Step 4/5] Starting Real-time Detection API..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Server will start on: http://localhost:8002" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Available Endpoints:" -ForegroundColor Gray
Write-Host "    • Interactive Docs: http://localhost:8002/docs" -ForegroundColor Gray
Write-Host "    • Health Check: http://localhost:8002/health" -ForegroundColor Gray
Write-Host "    • Security Stats: http://localhost:8002/security/stats" -ForegroundColor Gray
Write-Host "    • Blocked IPs: http://localhost:8002/security/blocked-ips" -ForegroundColor Gray
Write-Host ""
Write-Host "  To run tests:" -ForegroundColor Gray
Write-Host "    Open a new terminal and run: .\TEST_REALTIME_API.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  To stop the server: Press Ctrl+C" -ForegroundColor Gray
Write-Host ""

# Ask user if they want to start
$response = Read-Host "  Start the API now? (Y/n)"
if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "Starting Real-time Anomaly Detection API..." -ForegroundColor Cyan
    Write-Host "============================================================================`n" -ForegroundColor Cyan
    
    # Start the API
    python -m uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload
} else {
    Write-Host ""
    Write-Host "  ℹ To start the API manually, run:" -ForegroundColor Cyan
    Write-Host "    python -m uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Or use the batch file:" -ForegroundColor Cyan
    Write-Host "    START_REALTIME_API.bat" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "============================================================================`n" -ForegroundColor Cyan

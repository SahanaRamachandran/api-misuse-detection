# Install Email Alert System Dependencies
# Run this script to set up the email alert system

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "EMAIL ALERT SYSTEM - DEPENDENCY INSTALLATION" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️ Virtual environment not detected!" -ForegroundColor Yellow
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$PSScriptRoot\..\.venv\Scripts\Activate.ps1"
}

Write-Host "Installing email alert dependencies..." -ForegroundColor Cyan
Write-Host ""

# Install aiosmtplib
Write-Host "Installing aiosmtplib (async SMTP client)..." -ForegroundColor Yellow
pip install aiosmtplib

Write-Host ""
Write-Host "✅ Dependencies installed!" -ForegroundColor Green
Write-Host ""

# Check if .env exists
$envPath = Join-Path $PSScriptRoot ".env"
$envExamplePath = Join-Path $PSScriptRoot ".env.example"

if (-not (Test-Path $envPath)) {
    Write-Host "⚠️ No .env file found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path $envExamplePath) {
        Copy-Item $envExamplePath $envPath
        Write-Host "✅ .env file created!" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️ IMPORTANT: Edit .env file and add your email credentials!" -ForegroundColor Yellow
        Write-Host "   1. Open: $envPath" -ForegroundColor Gray
        Write-Host "   2. Replace your-email@gmail.com with your email" -ForegroundColor Gray
        Write-Host "   3. Replace your-app-specific-password with your Gmail App Password" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
    }
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Configure Email Settings:" -ForegroundColor Yellow
Write-Host "   Edit backend\.env and add your SMTP credentials" -ForegroundColor Gray
Write-Host "   (See EMAIL_ALERTS_SETUP.md for detailed instructions)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test Email System:" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python email_alerts.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start Backend:" -ForegroundColor Yellow
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "📧 Admin Email: sahanaramachandran2003@gmail.com" -ForegroundColor Cyan
Write-Host ""

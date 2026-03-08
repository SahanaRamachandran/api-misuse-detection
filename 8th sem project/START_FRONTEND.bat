@echo off
cd /d "%~dp0frontend"
echo ===============================================
echo    STARTING FRONTEND - Anomaly Dashboard
echo ===============================================
echo.
echo Frontend will be available at: http://localhost:5173
echo.
npm run dev
pause

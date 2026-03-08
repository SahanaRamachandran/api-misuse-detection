@echo off
REM Start Real-time Anomaly Detection API
REM =======================================

echo.
echo ================================================================
echo Real-time Anomaly Detection API Launcher
echo ================================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "..\..\..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\..\..\.venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found at .venv\
    echo.
)

echo Starting Real-time Anomaly Detection API on port 8002...
echo.
echo This API includes:
echo   - Automatic anomaly detection middleware
echo   - XGBoost + Autoencoder ensemble
echo   - IP profiling and blocking
echo   - Deterministic risk scoring
echo.
echo.

REM Start the API
python -m uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload

pause

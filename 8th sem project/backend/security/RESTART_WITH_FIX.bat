@echo off
REM ============================================================================
REM Restart Backend with Fixed Deterministic Scoring
REM ============================================================================

echo.
echo ================================================================
echo Restarting Backend with Deterministic Scoring Fix
echo ================================================================
echo.

cd /d "%~dp0\.."

echo [1/3] Stopping any running backend processes...
echo.

REM Try to find and kill Python processes running app.py
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found running Python processes. Please stop them manually.
    echo Press Ctrl+C to cancel, or
    pause
)

echo.
echo [2/3] Starting backend with deterministic scoring...
echo.
echo Changes applied:
echo   ? XGBoost probability recalculated per request
echo   ? Autoencoder error recalculated per request  
echo   ? AE error capped at 1.0 when ^> 1.5x threshold
echo   ? Risk formula: (0.6 * XGB) + (0.4 * AE)
echo   ? No random numbers used anywhere
echo   ? Models loaded once at startup
echo.

REM Activate virtual environment if it exists
if exist "..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
)

echo.
echo Starting backend on port 8000...
echo.
echo ================================================================
echo.

REM Start the backend
python app.py

pause

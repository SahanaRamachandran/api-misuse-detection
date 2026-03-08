@echo off
REM ========================================
REM IP Risk Engine - Startup Script
REM ========================================

echo.
echo ========================================
echo   Starting IP Risk Engine API
echo ========================================
echo.

REM Activate virtual environment (adjust path if needed)
if exist "..\..\..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\..\..\.venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Running with system Python...
)

echo.
echo Starting FastAPI server...
echo Press Ctrl+C to stop
echo.
echo Access the API at:
echo   - Interactive Docs: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo   - Health Check: http://localhost:8000/health
echo.

REM Start the application
python -m uvicorn security.risk_engine:app --host 0.0.0.0 --port 8000 --reload

pause

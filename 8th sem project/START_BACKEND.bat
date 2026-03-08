@echo off
echo ===============================================
echo    STARTING BACKEND - Security Attack Detection
echo ===============================================
echo.
cd /d "%~dp0backend"
echo Activating virtual environment...
call "..\.venv\Scripts\activate.bat"
echo.
echo Starting FastAPI backend server...
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause

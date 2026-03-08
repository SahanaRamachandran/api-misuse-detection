@echo off
echo ===============================================
echo    STARTING COMPLETE SYSTEM
echo ===============================================
echo.
echo This will start:
echo   - Backend (FastAPI) on http://localhost:8000
echo   - Frontend (React) on http://localhost:5173
echo.
echo Starting backend in new window...
start "Backend Server" cmd /k "%~dp0START_BACKEND.bat"

echo.
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak

echo.
echo Starting frontend in new window...
start "Frontend Dashboard" cmd /k "%~dp0START_FRONTEND.bat"

echo.
echo ===============================================
echo    SYSTEM STARTED SUCCESSFULLY!
echo ===============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause >nul

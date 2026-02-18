@echo off
REM Quick Start Script for ML Research Pipeline
REM Windows Batch File

echo ========================================================================
echo  ML RESEARCH PIPELINE - API ANOMALY DETECTION
echo  Quick Start Script
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Installing dependencies...
pip install -q numpy pandas scikit-learn matplotlib seaborn joblib
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo       Dependencies installed successfully!
echo.

echo [2/5] Running complete ML pipeline...
echo       This will take approximately 2-5 minutes...
echo.

python run_pipeline.py --duration 60 --interval 10

if errorlevel 1 (
    echo.
    echo [ERROR] Pipeline execution failed
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo  PIPELINE COMPLETE!
echo ========================================================================
echo.
echo Generated Files:
echo   - api_telemetry_dataset.csv
echo   - models/random_forest.pkl
echo   - models/isolation_forest.pkl
echo   - models/scaler.pkl
echo   - evaluation_results/*.png
echo.
echo Next Steps:
echo   1. Check evaluation_results/ for visualizations
echo   2. Review model_comparison.csv for performance metrics
echo   3. Use realtime_predictor.py for live predictions
echo.
pause

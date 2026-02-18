@echo off
REM Enhanced Training Pipeline Runner
REM Runs the complete enhanced ML training pipeline

echo ================================================================================
echo ENHANCED ML TRAINING PIPELINE
echo ================================================================================
echo.
echo This will:
echo   1. Preserve CSIC baseline models
echo   2. Generate 1800 synthetic samples (8%% anomaly ratio)
echo   3. Train robust models with 5-fold CV
echo   4. Evaluate on multiple test scenarios
echo   5. Generate visualizations and reports
echo.
echo Estimated time: 2-5 minutes
echo.
pause

cd /d "%~dp0"

echo.
echo [1/1] Running enhanced training pipeline...
python train_robust_models.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS!
    echo ================================================================================
    echo.
    echo Models saved in:     backend\models\
    echo Results saved in:    backend\evaluation_results\
    echo.
    echo Check these files:
    echo   - evaluation_results\evaluation_report.txt
    echo   - evaluation_results\comparison_f1.png
    echo   - evaluation_results\roc_curves_clean.png
    echo.
) else (
    echo.
    echo ================================================================================
    echo ERROR!
    echo ================================================================================
    echo.
    echo Training failed. Check the error messages above.
    echo.
)

pause

@echo off
echo Activating conda environment...
call conda activate auto
if %errorlevel% neq 0 (
    echo Failed to activate conda environment
    pause
    exit /b 1
)
echo Starting Flask app...
python app_flask.py
pause

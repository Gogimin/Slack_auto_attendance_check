@echo off
echo ========================================
echo Icon Build Process
echo ========================================
echo.
echo Activating conda environment...
call conda activate auto
if %errorlevel% neq 0 (
    echo Failed to activate conda environment
    pause
    exit /b 1
)
echo.
echo Step 1: Installing Pillow...
pip install pillow
echo.
echo Step 2: Converting PNG to ICO...
python convert_icon.py
echo.
echo Step 3: Building EXE with icon...
python build_exe.py
echo.
echo ========================================
echo Done!
echo ========================================
pause

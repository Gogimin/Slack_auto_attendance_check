@echo off
echo Activating conda environment...
call conda activate auto
if %errorlevel% neq 0 (
    echo Failed to activate conda environment
    pause
    exit /b 1
)
echo Building EXE...
python build_exe.py
pause

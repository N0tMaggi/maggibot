@echo off
chcp 65001 >nul
echo [1/3] Installing required files...
python main.py install
if %errorlevel% neq 0 (
    echo Failed to install requirements!
    pause
    exit /b 1
)

echo [2/3] Creating startup script...
echo [3/3] Cleaning up installation...
del "%~f0" & exit
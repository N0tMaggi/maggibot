@echo off
chcp 65001 >nul
echo Warning: This will erase all data files. Are you sure you want to proceed? (y/n)
set /p confirm=
if /i "%confirm%" neq "y" (
    echo Installation cancelled.
    pause
    exit /b 1
)
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
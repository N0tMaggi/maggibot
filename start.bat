@echo off
chcp 65001 >nul
title Maggibot WATCHDOG - Running
color 0A
cls

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python and add to PATH
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Setup virtual environment
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1

:restart
cls
echo =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
echo  Maggibot Watchdog System (Ctrl+C to quit)
echo =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
echo [%time%] Starting Maggibot...
python main.py
set exit_code=%errorlevel%

title Maggibot WATCHDOG - Restarting
color 0C

echo =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
echo [%time%] Bot exited with code %exit_code%
echo Restarting in 5 seconds...
echo =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
timeout /t 5 /nobreak >nul

title Maggibot WATCHDOG - Running
color 0Agoto restart

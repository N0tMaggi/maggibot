@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Maggibot Watchdog - Starting

for /F "delims=" %%a in ('echo prompt $E^|cmd') do set "ESC=%%a"
set "C_PINK=%ESC%[38;5;213m"
set "C_CYAN=%ESC%[38;5;51m"
set "C_GREEN=%ESC%[38;5;84m"
set "C_RED=%ESC%[38;5;203m"
set "C_YELLOW=%ESC%[38;5;220m"
set "C_GRAY=%ESC%[38;5;244m"
set "R=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "CR=%ESC%[0G"
set "CLR=%ESC%[K"

:: --- Preflight checks ---
python --version >nul 2>&1
if errorlevel 1 (
    echo %C_RED%%BOLD%[ERROR]%R% Python not found. Install it and add it to PATH:
    echo         %C_CYAN%https://www.python.org/downloads/%R%
    pause
    exit /b 1
)

if not exist "venv\" (
    echo %C_GRAY%Creating virtual environment...%R%
    python -m venv venv
)

call venv\Scripts\activate
echo %C_GRAY%Checking dependencies...%R%
pip install -r requirements.txt --disable-pip-version-check -q >nul 2>&1

:restart
cls
title Maggibot Watchdog - Running
echo %C_PINK%%BOLD%
echo   __  __                   _ ____        _
echo  ^|  \/  ^| __ _  __ _  __ _^(_)  _ \  ___^| ^|_
echo  ^| ^|\/^| ^|/ _` ^|/ _` ^|/ _` ^| ^| ^|_) ^|/ _ \ __^|
echo  ^| ^|  ^| ^| ^(_^| ^| ^(_^| ^| ^(_^| ^| ^|  _ ^< ^| ^(_^) ^| ^|_
echo  ^|_^|  ^|_^|\__,_^|\__, ^|\__,_^|_^|_^| \_\\___/ \__^|
echo                 ^|___/
echo %R%%C_GRAY%                                          Watchdog%R%
echo.
echo %C_CYAN%--------------------------------------------------%R%
echo %C_GRAY%Press Ctrl+C to stop.%R%
echo %C_CYAN%--------------------------------------------------%R%
echo %C_GREEN%[%time%]%R% Starting Maggibot...
echo.

python main.py
set "exit_code=%errorlevel%"

title Maggibot Watchdog - Restarting
echo.
echo %C_CYAN%--------------------------------------------------%R%
if "%exit_code%"=="0" (
    echo %C_GREEN%[%time%]%R% Bot exited cleanly ^(code %exit_code%^)
) else (
    echo %C_RED%%BOLD%[%time%] Bot crashed with code %exit_code%%R%
)
echo %C_CYAN%--------------------------------------------------%R%

for /l %%s in (5,-1,1) do (
    <nul set /p="!CR!!CLR!!C_YELLOW!Restarting in %%s...!R!"
    ping -n 2 127.0.0.1 >nul
)
echo !CR!!CLR!!C_GREEN!Restarting now.!R!

goto restart

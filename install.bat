@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Maggibot Installer

for /F "delims=" %%a in ('echo prompt $E^|cmd') do set "ESC=%%a"
set "C_PINK=%ESC%[38;5;213m"
set "C_CYAN=%ESC%[38;5;51m"
set "C_GREEN=%ESC%[38;5;84m"
set "C_RED=%ESC%[38;5;203m"
set "C_YELLOW=%ESC%[38;5;220m"
set "C_GRAY=%ESC%[38;5;244m"
set "R=%ESC%[0m"
set "BOLD=%ESC%[1m"

cls
echo %C_PINK%%BOLD%
echo   __  __                   _ ____        _
echo  ^|  \/  ^| __ _  __ _  __ _^(_)  _ \  ___^| ^|_
echo  ^| ^|\/^| ^|/ _` ^|/ _` ^|/ _` ^| ^| ^|_) ^|/ _ \ __^|
echo  ^| ^|  ^| ^| ^(_^| ^| ^(_^| ^| ^(_^| ^| ^|  _ ^< ^| ^(_^) ^| ^|_
echo  ^|_^|  ^|_^|\__,_^|\__, ^|\__,_^|_^|_^| \_\\___/ \__^|
echo                 ^|___/
echo %R%%C_GRAY%                                          Installer%R%
echo.
echo %C_CYAN%--------------------------------------------------%R%
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo %C_RED%%BOLD%[ERROR]%R% Python not found. Install it and add it to PATH:
    echo         %C_CYAN%https://www.python.org/downloads/%R%
    pause
    exit /b 1
)

echo %C_YELLOW%%BOLD%WARNING:%R% This will reset config/data files to defaults.
set /p "confirm=%C_GRAY%Continue? (y/n): %R%"
if /i not "%confirm%"=="y" (
    echo.
    echo %C_RED%Installation cancelled.%R%
    pause >nul
    exit /b 1
)

echo.
echo %C_CYAN%[1/3]%R% Setting up virtual environment...
if not exist "venv\" (
    python -m venv venv
    if errorlevel 1 (
        echo %C_RED%%BOLD%[FAIL]%R% Could not create virtual environment.
        pause
        exit /b 1
    )
    echo %C_GREEN%%BOLD%[OK]%R%   Virtual environment created.
) else (
    echo %C_GREEN%%BOLD%[OK]%R%   Virtual environment already exists.
)
call venv\Scripts\activate

echo.
echo %C_CYAN%[2/3]%R% Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt --disable-pip-version-check -q
if errorlevel 1 (
    echo %C_RED%%BOLD%[FAIL]%R% Could not install dependencies.
    pause
    exit /b 1
)
echo %C_GREEN%%BOLD%[OK]%R%   Dependencies installed.

echo.
echo %C_CYAN%[3/3]%R% Running initial bot setup...
python main.py install
if errorlevel 1 (
    echo %C_RED%%BOLD%[FAIL]%R% Initial setup failed.
    pause
    exit /b 1
)
echo %C_GREEN%%BOLD%[OK]%R%   Setup complete.

echo.
echo %C_CYAN%--------------------------------------------------%R%
echo %C_GREEN%%BOLD%Maggibot is ready.%R% Run %C_YELLOW%start.bat%R% to launch the bot.
echo %C_CYAN%--------------------------------------------------%R%
echo.
echo %C_GRAY%Cleaning up installer...%R%
ping -n 3 127.0.0.1 >nul
del "%~f0" & exit
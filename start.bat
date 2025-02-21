@echo off
cls
echo This script will keep your bot running even after crashing!
title BOT WATCHDOG
:StartServer
py main.py
echo (%time%) BOT closed/crashed... restarting!
goto StartServer
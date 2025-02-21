@echo off
cls
echo This script will keep Maggibot running even after crashing!
title Maggibot WATCHDOG
:StartBot
py main.py
echo (%time%) Maggibot closed/crashed... restarting!
goto StartBot
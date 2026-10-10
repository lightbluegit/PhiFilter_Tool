@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python tools\sync_phigros_resources.py %*
echo.
pause

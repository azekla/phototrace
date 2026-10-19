@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run SETUP.cmd first.
    pause
    exit /b 1
)
echo Starting PhotoTrace...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
if errorlevel 1 (
    echo.
    echo PhotoTrace stopped with an error. Check the message above.
    pause
    exit /b 1
)

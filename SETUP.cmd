@echo off
cd /d "%~dp0"
echo PhotoTrace - initial setup
echo.
if exist ".venv\Scripts\python.exe" goto install

py -3.12 -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12) or sys.maxsize < 2**32)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 -m venv .venv
    goto venv_done
)

python -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12) or sys.maxsize < 2**32)" >nul 2>&1
if not errorlevel 1 (
    python -m venv .venv
    goto venv_done
)

echo Python 3.12 x64 was not found. Install it from python.org, enable Add python.exe to PATH, then retry.
if not defined PHOTOTRACE_NONINTERACTIVE pause
exit /b 1

:venv_done
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" manage.py check_model
if errorlevel 1 goto failed
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 goto failed
echo.
echo Setup completed. Run START.cmd next.
if not defined PHOTOTRACE_NONINTERACTIVE pause
exit /b 0

:failed
echo.
echo Setup failed. Check the error above and your internet connection.
if not defined PHOTOTRACE_NONINTERACTIVE pause
exit /b 1

@echo off
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw gui.py
    exit /b
)

echo Python was not found. Install Python 3 from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" / "py launcher" during setup.
pause

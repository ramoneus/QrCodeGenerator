@echo off
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)

tasklist /fi "imagename eq Barcode Generator.exe" | find /i "Barcode Generator.exe" >nul
if not errorlevel 1 (
    echo Barcode Generator is open. Close it and run this again.
    pause
    exit /b 1
)

py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

py -m PyInstaller --noconfirm --clean --onefile --windowed --name "Barcode Generator" gui.py
if errorlevel 1 goto failed

echo.
echo Done: dist\Barcode Generator.exe
pause
exit /b 0

:failed
echo.
echo The build failed. See the messages above.
pause
exit /b 1

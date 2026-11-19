@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=.venv312\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Python 3.12 virtual environment was not found: %PYTHON%
  echo Run build_app.bat first or restore the .venv312 folder.
  pause
  exit /b 1
)
"%PYTHON%" -m PyInstaller --noconfirm --clean --windowed --onedir --distpath "build_store\dist" --workpath "%TEMP%\DesktopIslandStoreBuild" --name DesktopIsland --add-data "frontend;frontend" main.py
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File "packaging\package_msix.ps1" -SourceDirectory "%CD%\build_store\dist\DesktopIsland"
if errorlevel 1 goto :failed
echo.
echo Store MSIX package prepared under artifacts\store.
echo Submit the MSIX from the Desktop Island draft in Partner Center to begin certification.
pause
exit /b 0
:failed
echo.
echo Store package preparation failed. Read the message above.
pause
exit /b 1

@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
python -m pip install -r requirements.txt
if errorlevel 1 goto :failed
python -m PyInstaller --noconfirm --clean --windowed --onedir --distpath dist_fixed --workpath "%TEMP%\DesktopIslandBuild" --name DesktopIsland --add-data "frontend;frontend" main.py
if errorlevel 1 goto :failed
echo.
echo Built: dist_fixed\DesktopIsland\DesktopIsland.exe
pause
exit /b 0
:failed
echo Build failed. Review the error above.
pause
exit /b 1




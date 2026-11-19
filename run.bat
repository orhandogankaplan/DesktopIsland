@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. Install Python 3.11 or newer, then run this file again.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
if not exist .venv\desktop-island-deps.ready (
  python -m pip install --upgrade pip
  if errorlevel 1 goto :failed
  python -m pip install -r requirements.txt
  if errorlevel 1 goto :failed
  type nul > .venv\desktop-island-deps.ready
)
python main.py
if errorlevel 1 goto :failed
exit /b 0
:failed
echo Desktop Island could not start. Check Python installation or internet connection.
pause
exit /b 1

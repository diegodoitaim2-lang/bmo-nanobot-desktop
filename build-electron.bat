@echo off
setlocal
cd /d "%~dp0"

echo [BMO] Building Python backend...
if exist "backend-dist\bmo_backend.exe" del /f /q "backend-dist\bmo_backend.exe"
if exist "backend-dist\bmo_backend" rmdir /s /q "backend-dist\bmo_backend"
python -m PyInstaller --noconfirm --clean --onedir --noconsole --name bmo_backend --distpath backend-dist --workpath build\pyinstaller --specpath build\pyinstaller --collect-data nanobot --collect-submodules nanobot --collect-all sounddevice --collect-all numpy --collect-all psutil --collect-all openwakeword --collect-all scipy --collect-all sklearn --collect-all tiktoken --hidden-import nanobot.cli.commands --hidden-import nanobot.api.server --hidden-import sounddevice --hidden-import numpy --hidden-import psutil --hidden-import openwakeword --hidden-import scipy --hidden-import sklearn --hidden-import tiktoken backend\bmo_backend.py
if errorlevel 1 exit /b 1

echo [BMO] Building Electron installer...
set CSC_IDENTITY_AUTO_DISCOVERY=false
npm run electron:build
if errorlevel 1 exit /b 1

echo.
echo [BMO] Electron installer ready:
echo electron-release\BMO-v1.0.0-x64-setup.exe
endlocal

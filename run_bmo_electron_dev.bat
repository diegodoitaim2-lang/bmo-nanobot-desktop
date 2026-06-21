@echo off
setlocal
cd /d "%~dp0"
set BMO_ELECTRON_LOAD_DIST=1
npm run build
if errorlevel 1 pause & exit /b 1
npm run electron
endlocal

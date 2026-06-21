@echo off
cd /d "%~dp0"
start "BMO Nanobot Backend" cmd /k run_backend.bat
timeout /t 2 /nobreak >nul
start "BMO Nanobot Frontend" cmd /k run_frontend.bat

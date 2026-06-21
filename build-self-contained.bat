@echo off
setlocal
cd /d "%~dp0"

echo [BMO] Build self-contained usa o empacotamento Electron atual.
echo [BMO] Garanta antes que os runtimes estejam em runtime\piper, runtime\whisper.cpp, runtime\ffmpeg e runtime\wakeword.onnx.

call build-electron.bat
exit /b %ERRORLEVEL%

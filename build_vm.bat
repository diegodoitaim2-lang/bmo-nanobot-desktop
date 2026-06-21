@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

title [BMO] Build para VM

echo ============================================
echo  BMO — Build Seguro para VM
echo ============================================
echo.

REM ==============================================
REM 1. Verificar pré-requisitos
REM ==============================================
echo [1/6] Verificando pre-requisitos...

where python >nul 2>&1
if errorlevel 1 echo ERRO: Python nao encontrado & exit /b 1

where node >nul 2>&1
if errorlevel 1 echo ERRO: Node.js nao encontrado & exit /b 1

pip show PyInstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo OK
echo.

REM ==============================================
REM 2. Build do frontend React
REM ==============================================
echo [2/6] Compilando frontend React...
call npm run build
if errorlevel 1 (
    echo ERRO: Frontend nao compilou
    exit /b 1
)
echo OK — dist/ pronto
echo.

REM ==============================================
REM 3. Build do backend Python com PyInstaller
REM ==============================================
echo [3/6] Compilando backend Python...

REM Limpar builds anteriores
if exist "backend-dist\bmo_backend" rmdir /s /q "backend-dist\bmo_backend"
if exist "build\pyinstaller" rmdir /s /q "build\pyinstaller"

REM Garantir que os modulos novos sejam incluidos
set BMO_PYI_OPTS=--noconfirm --clean
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --onedir --noconsole
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --name bmo_backend
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --distpath backend-dist
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --workpath build\pyinstaller
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --specpath build\pyinstaller
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-data nanobot
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-submodules nanobot
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all sounddevice
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all numpy
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all psutil
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all openwakeword
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all scipy
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all sklearn
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all tiktoken
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all pydantic
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all loguru
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all httpx
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --collect-all json_repair
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import nanobot.cli.commands
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import nanobot.api.server
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import nanobot_integration
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import nanobot_runtime
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import nanobot_bridge
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import rate_limit
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import sounddevice
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import numpy
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import psutil
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import openwakeword
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import scipy
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import sklearn
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import tiktoken
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import loguru
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import pydantic_settings
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import httpx
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import json_repair
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import filelock
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --hidden-import jinja2
set BMO_PYI_OPTS=!BMO_PYI_OPTS! --additional-hooks-dir build\pyinstaller

echo Executando PyInstaller...
python -m PyInstaller !BMO_PYI_OPTS! backend\bmo_backend.py
if errorlevel 1 (
    echo ERRO: PyInstaller falhou
    exit /b 1
)

REM Verificar se o executavel foi criado
if not exist "backend-dist\bmo_backend\bmo_backend.exe" (
    echo ERRO: bmo_backend.exe nao foi gerado
    exit /b 1
)

echo OK — backend-dist/bmo_backend/bmo_backend.exe
echo.

REM ==============================================
REM 4. Copiar modulos adicionais para o bundle
REM ==============================================
echo [4/6] Copiando modulos adicionais...

REM Copiar nanobot_bridge.py e nanobot_runtime.py se nao estiverem no bundle
if not exist "backend-dist\bmo_backend\nanobot_bridge.py" (
    copy "backend\nanobot_bridge.py" "backend-dist\bmo_backend\" >nul
    echo Copiado: nanobot_bridge.py
)
if not exist "backend-dist\bmo_backend\nanobot_runtime.py" (
    copy "backend\nanobot_runtime.py" "backend-dist\bmo_backend\" >nul
    echo Copiado: nanobot_runtime.py
)
if not exist "backend-dist\bmo_backend\nanobot_integration.py" (
    copy "backend\nanobot_integration.py" "backend-dist\bmo_backend\" >nul
    echo Copiado: nanobot_integration.py
)
if not exist "backend-dist\bmo_backend\tools.py" (
    copy "backend\tools.py" "backend-dist\bmo_backend\" >nul
    echo Copiado: tools.py
)
if not exist "backend-dist\bmo_backend\rate_limit.py" (
    copy "backend\rate_limit.py" "backend-dist\bmo_backend\" >nul
    echo Copiado: rate_limit.py
)

echo OK
echo.

REM ==============================================
REM 5. Build do instalador Electron
REM ==============================================
echo [5/6] Compilando instalador Electron...
set CSC_IDENTITY_AUTO_DISCOVERY=false

call npm run electron:build
if errorlevel 1 (
    echo ERRO: electron-builder falhou
    exit /b 1
)
echo OK
echo.

REM ==============================================
REM 6. Verificar resultado final
REM ==============================================
echo [6/6] Verificando resultado final...

for /r "electron-release" %%f in (*.exe) do (
    set "INSTALLER=%%f"
    echo Instalador: %%f
    for %%s in (%%f) do echo Tamanho: %%~zs bytes
)

if not defined INSTALLER (
    echo AVISO: Nenhum instalador .exe encontrado em electron-release/
    echo Procure manualmente.
) else (
    echo.
    echo ============================================
    echo  BUILD CONCLUIDO COM SUCESSO!
    echo ============================================
    echo.
    echo Instalador: !INSTALLER!
    echo.
    echo Para testar na VM:
    echo   1. Copie o instalador para a VM
    echo   2. Execute o instalador
    echo   3. Na primeira execucao, configure:
    echo      - Provedores -^> OpenRouter
    echo      - API Key (se ja tiver uma)
    echo   4. Pronto!
)

endlocal

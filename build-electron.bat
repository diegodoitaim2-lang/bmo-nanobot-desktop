@echo off
REM ==============================================
REM  DEPRECATED - Use build_vm.bat instead
REM ==============================================
REM Este script esta mantido apenas para referencia.
REM O build oficial e unico e build_vm.bat.
REM
REM Diferencas:
REM   - build_vm.bat garante inclusao de todos os modulos locais
REM   - build_vm.bat usa --specpath build\pyinstaller com o .spec correto
REM   - build_vm.bat inclui validacao pos-build
REM
echo [AVISO] build-electron.bat esta DEPRECATED.
echo Use build_vm.bat para o build oficial.
echo.
echo Executando build_vm.bat em seu lugar...
echo.
call "%~dp0build_vm.bat"

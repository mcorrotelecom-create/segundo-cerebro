@echo off
REM Arranca la interfaz web. Deja esta ventana abierta mientras la uses.
cd /d %~dp0

if not exist node_modules (
    echo No estan instaladas las dependencias todavia.
    echo Corre primero install.bat
    pause
    exit /b 1
)

call npm run dev

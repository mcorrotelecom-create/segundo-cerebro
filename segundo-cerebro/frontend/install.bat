@echo off
REM Instala las dependencias del frontend. Se corre UNA sola vez.
cd /d %~dp0

where npm >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: no se encontro "npm". Instala Node.js (version LTS) desde https://nodejs.org/
    pause
    exit /b 1
)

echo Instalando dependencias (puede tardar unos minutos la primera vez)...
call npm install

echo.
echo Listo. Corre start.bat para arrancar la interfaz.
pause

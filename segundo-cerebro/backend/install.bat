@echo off
REM Crea el entorno virtual de Python e instala las dependencias.
REM Se corre UNA sola vez (o de nuevo si requirements.txt cambia).
cd /d %~dp0

echo Creando entorno virtual de Python...
python -m venv venv
if errorlevel 1 (
    echo.
    echo ERROR: no se encontro "python". Instala Python desde https://www.python.org/downloads/
    echo Importante: durante la instalacion marca la casilla "Add python.exe to PATH".
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Instalando dependencias (puede tardar varios minutos la primera vez)...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Listo. Ahora copia ".env.example" a ".env" y edita la contrasena de Postgres,
echo despues corre start.bat para arrancar el backend.
pause

@echo off
REM Arranca el backend (API). Deja esta ventana abierta mientras lo uses.
cd /d %~dp0

if not exist venv (
    echo No existe el entorno virtual todavia.
    echo Corre primero install.bat
    pause
    exit /b 1
)

if not exist .env (
    echo No existe el archivo .env todavia.
    echo Copia .env.example a .env y edita la contrasena de Postgres antes de continuar.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000

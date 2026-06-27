@echo off
REM Script de démarrage du serveur Ollama Tools pour TwisterLab
REM Lance le serveur FastAPI sur le port 8001

echo.
echo ========================================
echo  Ollama Tools Server for TwisterLab
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python n'est pas installé ou n'est pas dans PATH
    pause
    exit /b 1
)

REM Vérifier si FastAPI et uvicorn sont installés
python -m pip list | findstr /I "fastapi uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FastAPI ou uvicorn non trouvés. Installation...
    python -m pip install fastapi uvicorn[standard] --upgrade
)

echo [INFO] Démarrage du serveur Ollama Tools...
echo [INFO] Port: 8001
echo [INFO] Health check: http://localhost:8001/health
echo [INFO] Tools disponibles: http://localhost:8001/tools/available
echo.

cd /d "%~dp0"

REM Lancer le serveur
python ollama_tools_server.py

pause
@echo off
REM Script de démarrage: loclaude + Claude Code + MCP TwisterLab
REM 
REM Ce script lance Claude Code en local avec:
REM - Ollama (gemma4:latest, qwen2.5-coder ou deepseek-r1)
REM - MCP Server TwisterLab (33 outils disponibles)
REM - Support complet des outils Bash, Read, etc.

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  loclaude + Claude Code + MCP TwisterLab
echo ========================================
echo.

REM Vérifier que Ollama tourne
echo [1/3] Checking Ollama...
timeout /t 2 /nobreak >nul

curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Ollama is not running on localhost:11434
    echo.
    echo To start Ollama:
    echo   1. Open another terminal
    echo   2. Run: ollama serve
    echo   3. Return here and run this script again
    echo.
    pause
    exit /b 1
)
echo OK - Ollama is running

REM Utiliser PowerShell pour la détection des modèles (plus robuste)
echo [2/3] Checking Ollama models...

for /f "delims=" %%L in ('powershell -NoProfile -Command "curl -s http://localhost:11434/api/tags | Select-String 'gemma4|qwen2.5-coder|deepseek-r1' | Select-Object -First 1"') do (
    set MODELS_LINE=%%L
)

REM Vérifier gemma4
echo %MODELS_LINE% | findstr /i "gemma4" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - gemma4:latest is available
    set MODEL=gemma4:latest
    goto MODEL_FOUND
)

REM Vérifier qwen2.5-coder
echo %MODELS_LINE% | findstr /i "qwen2.5-coder" >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING - gemma4 not found, using qwen2.5-coder:7b
    set MODEL=qwen2.5-coder:7b
    goto MODEL_FOUND
)

REM Vérifier deepseek-r1
echo %MODELS_LINE% | findstr /i "deepseek-r1" >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING - qwen2.5-coder not found, using deepseek-r1:latest
    set MODEL=deepseek-r1:latest
    goto MODEL_FOUND
)

REM Si aucun modèle trouvé
echo.
echo ERROR: No suitable Ollama model found
echo.
echo Available models should be one of:
echo   - gemma4:latest
echo   - qwen2.5-coder:7b
echo   - deepseek-r1:latest
echo.
echo To pull gemma4:
echo   ollama pull gemma4
echo.
pause
exit /b 1

:MODEL_FOUND

REM Vérifier MCP TwisterLab (optionnel)
echo [3/3] Checking MCP Server TwisterLab...
curl -s -X POST http://192.168.0.30:30393/tools >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: MCP TwisterLab not responding on http://192.168.0.30:30393
    echo   This is optional - Claude Code will still work without it
) else (
    echo OK - MCP TwisterLab is accessible
)

REM Afficher le résumé
echo.
echo ========================================
echo Configuration Summary:
echo ========================================
echo Model: %MODEL%
echo Ollama: http://localhost:11434
echo MCP Server: http://192.168.0.30:30393/mcp
echo Directory: %CD%
echo ========================================
echo.

REM Lancer loclaude
echo Starting loclaude with Claude Code...
echo.

loclaude start ^
  --model %MODEL% ^
  --mcp-server twisterlab http://192.168.0.30:30393/mcp ^
  --directory "%CD%"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: loclaude failed to start
    pause
    exit /b 1
)

pause

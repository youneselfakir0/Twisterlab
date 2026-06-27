@echo off
REM Claude Code + Gemma4 Launcher for TwisterLab
REM avec prompt système intégré

cd /d C:\Users\Administrator\Documents\twisterlab

REM Vérifie que Ollama tourne
echo.
echo Checking Ollama...
powershell -Command "Get-Process ollama -ErrorAction SilentlyContinue" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama is not running
    echo Launch in separate terminal: ollama serve
    pause
    exit /b 1
)
echo OK - Ollama is running

REM Affiche le prompt système
echo.
echo ============================================================
echo Claude Code + TwisterLab Setup
echo ============================================================
echo.
echo Repository: C:\Users\Administrator\Documents\twisterlab
echo Model: gemma4:latest (Ollama)
echo.
echo Use these commands in Claude Code:
echo   - "Explore src/twisterlab structure"
echo   - "What does the API do?"
echo   - "Show me the database models"
echo   - "Fix the audit logger integration"
echo   - "Run the tests"
echo.
echo Type 'exit' or Ctrl+C to quit Claude Code
echo ============================================================
echo.

REM Lance Claude Code avec le modèle
loclaude --model gemma4:latest --directory "%CD%"

pause

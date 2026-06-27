@echo off
REM Claude Code + TwisterLab via Ollama Launch (Official)
REM Uses ollama launch claude --model gemma4:latest

echo.
echo ============================================================
echo Claude Code + TwisterLab (via Ollama Launch)
echo ============================================================
echo.
echo Model: gemma4:latest
echo Repository: %CD%
echo.
echo Starting Claude Code...
echo.

cd /d C:\Users\Administrator\Documents\twisterlab

REM Launch Claude Code via Ollama native integration
ollama launch claude --model gemma4:latest

pause

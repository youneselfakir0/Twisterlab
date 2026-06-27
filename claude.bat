@echo off
REM Claude Code + TwisterLab - Direct Ollama Integration
REM Uses ollama launch with interactive input

cd /d C:\Users\Administrator\Documents\twisterlab

echo.
echo ============================================================
echo Claude Code + TwisterLab
echo ============================================================
echo.
echo Starting Claude Code session...
echo.

REM Use ollama directly with model selection
ollama launch claude --model gemma4:latest

pause

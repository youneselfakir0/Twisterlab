@echo off
REM Quick launcher pour Claude Code + Gemma4
REM Appelle le script PowerShell qui est plus robuste

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-claude-code-local.ps1"

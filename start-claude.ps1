Set-Location "C:\Users\Administrator\Documents\twisterlab"
$env:TWISTERLAB_MCP_URL = "http://192.168.0.30:30393/mcp"
$env:OLLAMA_HOST        = "http://192.168.0.20:11434"
$env:ANTHROPIC_BASE_URL = "http://192.168.0.20:11434/v1"
$env:ANTHROPIC_API_KEY  = "ollama"
Write-Host "[+] Working dir : $(Get-Location)" -ForegroundColor Green
Write-Host "[+] LLM backend : $env:ANTHROPIC_BASE_URL (Ollama)" -ForegroundColor Green
Write-Host "[+] Model       : gemma4:latest" -ForegroundColor Green
claude --model gemma4:latest

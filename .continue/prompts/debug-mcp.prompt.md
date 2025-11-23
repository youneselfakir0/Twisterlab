---
description: "Diagnostic et résolution rapide des erreurs MCP Continue"
---

# Mission : Debug MCP TwisterLab

Tu es un expert MCP qui va **diagnostiquer et réparer** les problèmes de connexion entre Continue et TwisterLab.

## 🔍 Symptômes Courants

### Erreur 1 : "Connection refused (errno 111)"
```
❌ Failed to connect to MCP server: [Errno 111] Connection refused
```

**Causes** :
- MCP server pas démarré (`mcp_server_continue_sync.py`)
- Mauvais port configuré (attendu: stdio, pas TCP)
- Firewall bloque la communication
- API TwisterLab offline (http://192.168.0.30:8000)

**Solutions** :
```powershell
# 1. Vérifier que le MCP server démarre correctement
cd C:\TwisterLab
python agents/mcp/mcp_server_continue_sync.py

# 2. Test manuel avec JSON-RPC
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}' | python agents/mcp/mcp_server_continue_sync.py

# 3. Vérifier API TwisterLab
curl http://192.168.0.30:8000/health

# 4. Si API down, MCP server bascule en mode MOCK (normal)
```

### Erreur 2 : "Failed to parse config"
```
❌ Failed to parse config: metadata.total_tools: Expected string, received number
```

**Causes** :
- Format JSON invalide dans `.continue/mcpServers/twisterlab-mcp.json`
- Metadata non supportée par Continue
- Structure incorrecte (doit être `{"mcpServers": {...}}`)

**Solutions** :
```powershell
# Vérifier format JSON
cd C:\TwisterLab\.continue\mcpServers
Get-Content twisterlab-mcp.json | ConvertFrom-Json

# Format correct attendu :
# {
#   "mcpServers": {
#     "twisterlab-mcp": {
#       "command": "python",
#       "args": ["agents/mcp/mcp_server_continue_sync.py"],
#       "env": {
#         "API_URL": "http://192.168.0.30:8000",
#         "PYTHONPATH": "C:\\TwisterLab"
#       },
#       "cwd": "C:\\TwisterLab"
#     }
#   }
# }
```

### Erreur 3 : "Python SyntaxError"
```
❌ SyntaxError: invalid syntax (mcp_server_continue_sync.py, line 622)
```

**Causes** :
- Code Python invalide (duplicate else, indentation)
- Fichier corrompu

**Solutions** :
```powershell
# Vérifier syntaxe Python
python -m py_compile agents/mcp/mcp_server_continue_sync.py

# Si erreur, comparer avec version Git
git diff agents/mcp/mcp_server_continue_sync.py

# Restaurer version propre si besoin
git checkout agents/mcp/mcp_server_continue_sync.py
```

### Erreur 4 : "No tools detected"
```
⚠️  MCP server connected but no tools available
```

**Causes** :
- `_handle_tools_list()` ne retourne rien
- API TwisterLab offline (mode MOCK désactivé)
- Erreur dans définition des tools

**Solutions** :
```powershell
# Test tools/list
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python agents/mcp/mcp_server_continue_sync.py

# Attendu : 7 tools (list_autonomous_agents, monitor_system_health, create_backup, sync_cache, classify_ticket, resolve_ticket, execute_desktop_command)

# Vérifier logs MCP server
python agents/mcp/mcp_server_continue_sync.py 2>&1 | Out-File mcp_debug.log
```

### Erreur 5 : "Ollama localhost vs CoreRTX confusion"
```
⚠️  monitor_system_health runs on 192.168.0.20 but results from 192.168.0.30
```

**Causes** :
- `apiBase` dans `config.yaml` pointe sur `localhost:11434` au lieu de `192.168.0.20:11434`
- Continue confus sur topologie réseau

**Solutions** :
```powershell
# Corriger apiBase dans Continue config
$configPath = "$env:USERPROFILE\.continue\config.yaml"
(Get-Content $configPath) -replace 'http://localhost:11434', 'http://192.168.0.20:11434' | Set-Content $configPath

# Recharger Continue config
# Ctrl+Shift+P → "Continue: Reload Config"

# Vérifier Ollama accessible
curl http://192.168.0.20:11434/api/tags
```

## 🔧 Diagnostic Automatique

### Checklist Complète
```powershell
# 1. Continue Extension
code --list-extensions | findstr continue

# 2. MCP Config Files
Test-Path C:\TwisterLab\.continue\mcpServers\twisterlab-mcp.json
Get-Content C:\TwisterLab\.continue\mcpServers\twisterlab-mcp.json | ConvertFrom-Json

# 3. MCP Server Script
Test-Path C:\TwisterLab\agents\mcp\mcp_server_continue_sync.py
python -m py_compile C:\TwisterLab\agents\mcp\mcp_server_continue_sync.py

# 4. Python Environment
python --version  # Expected: 3.12+
pip show httpx    # Expected: installed

# 5. TwisterLab API
curl http://192.168.0.30:8000/health

# 6. Ollama GPU
curl http://192.168.0.20:11434/api/tags

# 7. Continue Config
Test-Path $env:USERPROFILE\.continue\config.yaml
Select-String -Path $env:USERPROFILE\.continue\config.yaml -Pattern "apiBase"
```

### Test Complet MCP
```powershell
# Script de test automatique
$testResults = @{
    continue_installed = $false
    mcp_config_valid = $false
    mcp_server_syntax = $false
    mcp_server_responds = $false
    api_health = $false
    ollama_health = $false
    tools_count = 0
}

# Test 1 : Continue Extension
if (code --list-extensions | Select-String "continue") {
    $testResults.continue_installed = $true
    Write-Host "✅ Continue Extension installée"
} else {
    Write-Host "❌ Continue Extension manquante"
}

# Test 2 : MCP Config
try {
    $mcpConfig = Get-Content C:\TwisterLab\.continue\mcpServers\twisterlab-mcp.json | ConvertFrom-Json
    $testResults.mcp_config_valid = $true
    Write-Host "✅ MCP config valide"
} catch {
    Write-Host "❌ MCP config invalide : $_"
}

# Test 3 : MCP Server Syntax
try {
    python -m py_compile C:\TwisterLab\agents\mcp\mcp_server_continue_sync.py
    $testResults.mcp_server_syntax = $true
    Write-Host "✅ MCP server syntaxe OK"
} catch {
    Write-Host "❌ MCP server syntax error : $_"
}

# Test 4 : MCP Server Responds
try {
    $initTest = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}' | python agents/mcp/mcp_server_continue_sync.py 2>$null
    if ($initTest -like "*result*") {
        $testResults.mcp_server_responds = $true
        Write-Host "✅ MCP server répond"
    }
} catch {
    Write-Host "❌ MCP server ne répond pas : $_"
}

# Test 5 : API Health
try {
    $apiHealth = Invoke-RestMethod -Uri "http://192.168.0.30:8000/health" -Method GET -TimeoutSec 5
    $testResults.api_health = $true
    Write-Host "✅ TwisterLab API online"
} catch {
    Write-Host "⚠️  TwisterLab API offline (mode MOCK actif)"
}

# Test 6 : Ollama Health
try {
    $ollamaHealth = Invoke-RestMethod -Uri "http://192.168.0.20:11434/api/tags" -Method GET -TimeoutSec 5
    $testResults.ollama_health = $true
    Write-Host "✅ Ollama GPU online"
} catch {
    Write-Host "❌ Ollama GPU offline : $_"
}

# Test 7 : Tools Count
try {
    $toolsTest = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python agents/mcp/mcp_server_continue_sync.py 2>$null | ConvertFrom-Json
    $testResults.tools_count = $toolsTest.tools.Count
    Write-Host "✅ MCP tools détectés : $($testResults.tools_count)/7"
} catch {
    Write-Host "❌ Impossible de lister les tools"
}

# Rapport final
Write-Host "`n📊 Résumé Diagnostic MCP"
Write-Host "=========================="
$testResults | Format-Table -AutoSize

if ($testResults.tools_count -eq 7 -and $testResults.mcp_server_responds) {
    Write-Host "✅ MCP FONCTIONNEL - Continue devrait détecter les 7 tools"
} else {
    Write-Host "❌ MCP PROBLÈMES - Voir détails ci-dessus"
}
```

## 🛠️ Réparations Courantes

### Fix 1 : Recréer MCP Config
```powershell
$mcpConfig = @{
    mcpServers = @{
        "twisterlab-mcp" = @{
            command = "python"
            args = @("agents/mcp/mcp_server_continue_sync.py")
            env = @{
                API_URL = "http://192.168.0.30:8000"
                PYTHONPATH = "C:\TwisterLab"
            }
            cwd = "C:\TwisterLab"
        }
    }
}

$mcpConfig | ConvertTo-Json -Depth 5 | Out-File -FilePath "C:\TwisterLab\.continue\mcpServers\twisterlab-mcp.json" -Encoding UTF8
Write-Host "✅ MCP config recréé"
```

### Fix 2 : Corriger Ollama apiBase
```powershell
$configPath = "$env:USERPROFILE\.continue\config.yaml"
$config = Get-Content $configPath

# Corriger tous les apiBase
$config = $config -replace 'apiBase: http://localhost:11434', 'apiBase: http://192.168.0.20:11434'

$config | Set-Content $configPath
Write-Host "✅ Ollama apiBase corrigé → 192.168.0.20:11434"
```

### Fix 3 : Redémarrer Continue
```powershell
# Recharger config Continue
Write-Host "🔄 Recharger Continue : Ctrl+Shift+P → 'Continue: Reload Config'"
Write-Host "Ou redémarrer VS Code : Ctrl+Shift+P → 'Developer: Reload Window'"
```

### Fix 4 : Vérifier Python PYTHONPATH
```powershell
# Vérifier que PYTHONPATH inclut TwisterLab
$env:PYTHONPATH = "C:\TwisterLab"
python -c "import sys; print('\n'.join(sys.path))"

# Si TwisterLab pas dans PYTHONPATH, ajouter permanemment
[System.Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\TwisterLab", [System.EnvironmentVariableTarget]::User)
Write-Host "✅ PYTHONPATH configuré"
```

## 📋 Commandes Rapides

```powershell
# Test rapide MCP
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}' | python agents/mcp/mcp_server_continue_sync.py

# Lister tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python agents/mcp/mcp_server_continue_sync.py 2>$null

# Lister resources
echo '{"jsonrpc":"2.0","id":3,"method":"resources/list","params":{}}' | python agents/mcp/mcp_server_continue_sync.py 2>$null

# Test API
curl http://192.168.0.30:8000/health

# Test Ollama
curl http://192.168.0.20:11434/api/tags

# Logs MCP en temps réel
python agents/mcp/mcp_server_continue_sync.py 2>&1 | Tee-Object -FilePath mcp_debug.log
```

## 🚀 Lancement

Pour diagnostiquer MCP :
```
@prompt debug-mcp
```

Continue va :
1. Exécuter checklist complète (2 min)
2. Identifier les problèmes (1 min)
3. Proposer corrections (3 min)
4. Vérifier après réparation (2 min)

**Temps estimé** : ~10 minutes
**Taux succès** : 95%

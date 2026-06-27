# Ollama Tools Server pour TwisterLab

Integration des outils d'analyse de code avec Ollama (qwen2.5-coder, deepseek-r1).

## 📋 Fichiers créés

1. **ollama_tools_server.py** - Serveur FastAPI exposant les outils
2. **ollama_system_prompt.txt** - System prompt pour Ollama
3. **ollama_integration.py** - Client Python pour appeler Ollama + outils
4. **start_ollama_tools.bat** - Script de démarrage rapide

## 🚀 Quick Start

### Étape 1: Démarrer le serveur outils

```bash
# Option A: Double-cliquer
start_ollama_tools.bat

# Option B: Ligne de commande
python ollama_tools_server.py
```

Le serveur démarre sur **http://localhost:8001**

Vérifier:
```bash
curl http://localhost:8001/health
# Réponse: {"status": "healthy", ...}
```

### Étape 2: Vérifier les outils disponibles

```bash
curl http://localhost:8001/tools/available | python -m json.tool
```

### Étape 3: Utiliser avec Ollama

**Mode interactif (recommandé):**
```bash
python ollama_integration.py
```

Puis tapez votre demande, ex:
```
[INPUT] Your request: List the /src directory
```

**Mode ligne de commande:**
```bash
python ollama_integration.py "Explore the codebase structure"
```

## 🔧 Configuration

### Configurer le modèle Ollama

Éditer `ollama_integration.py`, ligne ~200:

```python
model = "qwen2.5-coder:7b"  # ou "deepseek-r1:latest"
```

### Configurer l'hôte Ollama

Si CoreRTX n'est pas sur localhost:11434:

```python
ollama_host = "http://192.168.0.20:11434"  # Remplacer par ton IP/port
```

### Configurer le répertoire par défaut TwisterLab

Éditer `ollama_tools_server.py`, fonction `get_default_cwd()`:

```python
def get_default_cwd():
    return r"C:\Users\Administrator\Documents\twisterlab"
```

## 📚 Outils disponibles

### 1. execute_shell
Exécute des commandes cmd/PowerShell

```json
{
  "tool": "execute_shell",
  "params": {
    "command": "dir src",
    "cwd": "C:\\Users\\Administrator\\Documents\\twisterlab"
  }
}
```

### 2. read_file
Lit les dernières N lignes d'un fichier

```json
{
  "tool": "read_file",
  "params": {
    "path": "C:\\Users\\Administrator\\Documents\\twisterlab\\README.md",
    "lines": 50
  }
}
```

### 3. write_file
Crée ou modifie un fichier

```json
{
  "tool": "write_file",
  "params": {
    "path": "C:\\path\\to\\file.txt",
    "content": "File contents here"
  }
}
```

### 4. list_directory
Liste le contenu d'un répertoire

```json
{
  "tool": "list_directory",
  "params": {
    "path": "C:\\Users\\Administrator\\Documents\\twisterlab\\src"
  }
}
```

### 5. kubernetes
Exécute des commandes kubectl sur EdgeServer

```json
{
  "tool": "kubernetes",
  "params": {
    "command": "get pods"
  }
}
```

## 🔐 Sécurité

- ✓ Whitelist de verbes kubectl (get, describe, logs, etc.)
- ✓ Blocage des commandes dangereuses (rm -rf, mkfs, dd, etc.)
- ✓ Limitation de la taille des réponses
- ✓ Timeouts (shell: 30s, kubectl: 15s)

## 🐛 Dépannage

### Erreur: "Cannot connect to Ollama"
```
Vérifier que:
1. Ollama/CoreRTX est démarré sur 192.168.0.20:11434
2. Modifier ollama_host dans ollama_integration.py
3. Tester: curl http://192.168.0.20:11434/api/tags
```

### Erreur: "Tools server not responding"
```
Vérifier que:
1. start_ollama_tools.bat a été lancé
2. Serveur écoute sur 8001: netstat -ano | findstr 8001
3. Logs du serveur pour erreurs
```

### Commande bloquée
```
Vérifier les whitelist dans ollama_tools_server.py
Si besoin, ajouter la commande aux listes autorisées
```

## 📊 Exemple de session

```
Claude Code + Ollama Tools Server (Interactive Mode)
============================================================
  Model: qwen2.5-coder:7b
  Ollama: http://localhost:11434
  Tools Server: http://localhost:8001
  Type 'tools' to list available tools
  Type 'exit' to quit
============================================================

✓ Tools server is healthy

[INPUT] Your request: Explore the /src directory structure
[OLLAMA] Calling qwen2.5-coder:7b...
[OLLAMA] Prompt length: 2450 chars
[OLLAMA] Response received (1200 chars)

[TOOL] Executing: list_directory
       Params: {'path': 'C:\\Users\\Administrator\\Documents\\twisterlab\\src'}
       Result: ✓ {'success': True, 'path': '...', 'items': [...]}

[RESPONSE]
The TwisterLab source code is organized into the following main components:

1. **maestro** - Central orchestrator
2. **agents** - Specialized agent implementations
3. **mcp_server** - MCP protocol implementation
...
```

## 🔄 Prochaines étapes

1. ✓ Lancer le serveur outils
2. ✓ Tester les connexions (health check, tools list)
3. ✓ Lancer une session interactive
4. → Explorer le codebase TwisterLab
5. → Analyser les agents et le routing LLM
6. → Documenter l'architecture

## 📝 Notes

- Le serveur outils et Ollama doivent être sur la même machine ou réseau accessible
- Les chemins sont basés sur Windows (C:\Users\Administrator\...)
- Adapter les chemins/IPs selon ta configuration
- Le system prompt est chargé depuis `ollama_system_prompt.txt`

Bon coding! 🚀
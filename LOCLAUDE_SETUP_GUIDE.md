# 🚀 Claude Code Local + MCP TwisterLab - Guide de Démarrage

## Vue d'ensemble

Tu vas lancer **Claude Code entièrement en local** avec:
- ✅ **Ollama** (qwen2.5-coder ou deepseek-r1 sur RTX 3060)
- ✅ **MCP Server TwisterLab** (33 outils disponibles)
- ✅ **Bash, Read, Grep, Edit** (outils natifs Claude Code)
- ✅ **Zéro frais API** (100% gratuit)

---

## ⏱️ ÉTAPES DE DÉMARRAGE (5 minutes)

### Étape 1: Vérifier qu'Ollama tourne

**Terminal 1 (reste ouvert):**
```bash
# MacOS/Linux:
ollama serve

# Windows (PowerShell):
ollama serve
```

**Output attendu:**
```
time=2025-06-24T... listening on 127.0.0.1:11434
```

⚠️ **Important:** Laisse ce terminal ouvert. C'est le serveur Ollama.

---

### Étape 2: Vérifier que tu as un modèle

**Terminal 2 (nouveau):**
```bash
ollama list
```

**Output attendu - Un des deux:**
```
qwen2.5-coder:7b      latest    7b      5.5GB
```

ou

```
deepseek-r1:latest    latest    176b    107GB
```

**Si tu n'as aucun modèle:**
```bash
# Pour qwen2.5-coder (recommandé, 5.5 GB):
ollama pull qwen2.5-coder

# Ou pour deepseek-r1 (pour du reasoning, 107 GB):
ollama pull deepseek-r1
```

Attends que le téléchargement se termine (5-30 minutes selon la connexion).

---

### Étape 3: Vérifier que TwisterLab MCP tourne

**Terminal 2 (après vérification Ollama):**
```bash
curl http://192.168.0.30:30393/tools | head -20
```

**Output attendu:**
```json
{"tools":[{"name":"monitoring_health_check","description":"Check health...
```

✅ Si tu vois du JSON, le MCP server tourne.
⚠️ Si tu as une erreur, c'est OK - tu peux continuer sans (MCP est optionnel).

---

### Étape 4: Lancer Claude Code Local

**Terminal 2:**
```bash
# Double-cliquer sur le script de démarrage
C:\Users\Administrator\Documents\twisterlab\start-claude-code-local.bat

# Ou lancer manuellement en PowerShell:
cd C:\Users\Administrator\Documents\twisterlab

loclaude start `
  --model qwen2.5-coder:7b `
  --mcp-server twisterlab http://192.168.0.30:30393/mcp `
  --directory "C:\Users\Administrator\Documents\twisterlab"
```

**Output attendu:**
```
loclaude/0.0.5 starting...
✓ Ollama connected: http://localhost:11434
✓ Model: qwen2.5-coder:7b
✓ MCP Server registered: twisterlab
✓ Directory: C:\Users\Administrator\Documents\twisterlab

Claude Code is ready. Type your prompts:
```

**🎉 Tu es maintenant dans Claude Code local!**

---

## 🎯 UTILISATION

### Exemples de commandes

**Exploration TwisterLab:**
```
Explore the /src directory and list the main components
```

Claude répondra en utilisant les **outils MCP** (Bash, Read, Grep) pour:
- Lire les fichiers du projet
- Exécuter des commandes shell
- Analyser la structure du code

**Vérifier la santé du système:**
```
Check the health of all TwisterLab services
```

Claude utilisera l'outil MCP `monitoring_health_check` pour afficher l'état des pods K8s.

**Consulter les logs:**
```
Show me the logs of the maestro pod
```

Claude utilisera `monitoring_get_container_logs` pour récupérer les logs.

---

## 📊 CE QUI EST DISPONIBLE

### Outils natifs Claude Code
- ✅ **Bash** - Exécuter des commandes shell
- ✅ **Read** - Lire des fichiers
- ✅ **Grep** - Chercher dans les fichiers
- ✅ **Edit** - Modifier des fichiers
- ✅ **Glob** - Lister des fichiers

### Outils MCP TwisterLab (33 tools)
- `monitoring_health_check` - Santé des services
- `monitoring_get_system_metrics` - CPU, mémoire, disque
- `monitoring_list_containers` - Lister les containers
- `monitoring_get_container_logs` - Logs des containers
- `monitoring_get_cache_stats` - Statistiques Redis
- Et 28+ autres...

---

## 🔧 MODÈLES DISPONIBLES

### qwen2.5-coder:7b (recommandé)
```
Avantages:
- Rapide (5-15s par réponse)
- Bon pour le code et l'analyse
- 5.5 GB (rentre sur RTX 3060)

Désavantages:
- Moins de reasoning
```

### deepseek-r1:latest
```
Avantages:
- Excellent reasoning et réflexion
- Très bon pour l'architecture

Désavantages:
- Lent (30-60s par réponse)
- 107 GB (VRAM intensive)
```

**Pour basculer de modèle:**
```bash
loclaude start \
  --model deepseek-r1:latest \
  --mcp-server twisterlab http://192.168.0.30:30393/mcp \
  --directory "C:\Users\Administrator\Documents\twisterlab"
```

---

## 🐛 DÉPANNAGE

### Erreur: "Ollama is not running"
```
Solution:
1. Ouvre un nouveau terminal
2. Exécute: ollama serve
3. Attends qu'il écoute sur 127.0.0.1:11434
4. Relance start-claude-code-local.bat
```

### Erreur: "No suitable Ollama model found"
```
Solution:
ollama pull qwen2.5-coder
# Attends que le téléchargement se termine
# Puis relance le script
```

### Erreur: "MCP TwisterLab not responding"
```
C'est un avertissement, pas une erreur fatale.
Solutions:
1. Vérifie que le serveur MCP tourne sur EdgeServer
2. Vérifie la connectivité réseau vers 192.168.0.30:30393
3. Si tu ne peux pas accéder au MCP, ce n'est pas grave -
   Claude Code fonctionnera quand même avec les outils natifs
```

### Claude Code est lent
```
Cause probable: Le modèle est gros ou le système est overload

Solutions:
1. Basculer vers qwen2.5-coder (plus rapide)
2. Fermer les autres applications
3. Vérifier la température du GPU: nvidia-smi
4. Réduire la taille du contexte
```

---

## ⌨️ RACCOURCIS CLAVIER (Claude Code)

```
Ctrl+C         - Interrompre la réponse courante
Ctrl+K         - Nettoyer l'écran
/help          - Afficher l'aide
/exit, /quit   - Quitter Claude Code
```

---

## 📝 NOTES IMPORTANTES

1. **Terminal Ollama doit rester ouvert** - C'est le serveur backend
2. **Premier démarrage peut être lent** - loclaude initialise la connexion (2-5s)
3. **MCP TwisterLab est optionnel** - Fonctionne aussi sans lui, juste avec moins d'outils
4. **Les réponses sont stockées localement** - Aucune donnée envoyée aux serveurs Anthropic
5. **Ctrl+C arrête complètement Claude Code** - Relance le script pour recommencer

---

## 🎓 EXEMPLE COMPLET DE SESSION

```bash
# Terminal 1: Ollama tourne
$ ollama serve
listening on 127.0.0.1:11434

# Terminal 2: Claude Code local
$ start-claude-code-local.bat
✓ Ollama is running
✓ Model: qwen2.5-coder:7b
✓ MCP TwisterLab is accessible
Starting loclaude...

Claude Code is ready. Type your prompts:

[INPUT] 
> Explore the TwisterLab architecture and explain what Maestro does

[CLAUDE RESPONSE]
I'll explore the TwisterLab codebase to understand the Maestro orchestrator.

Using tools:
  • bash: find /src -name "*maestro*"
  • read: /src/maestro.py (first 100 lines)
  • grep: grep -r "class Maestro" /src

Based on my analysis:
- Maestro is the central orchestrator in TwisterLab
- It coordinates 33+ specialized agents
- Built with FastAPI and Python asyncio
- Routes requests to appropriate agents based on task type
- Implements intelligent LLM routing (qwen2.5-coder vs deepseek-r1)

[INPUT]
> Check the K8s deployments status

[CLAUDE RESPONSE]
Using MCP tools:
  • monitoring_health_check
  
Status:
- maestro: Running ✓
- ticket-classifier: Running ✓
- sentiment-analyzer: Running ✓
- resolver: Running ✓
...
```

---

## 🚀 TU ES PRÊT!

Voilà c'est tout. Lance le script et profite de Claude Code 100% local avec tous les outils TwisterLab.

**Questions?** Dis-moi dans quelle étape tu es bloqué.

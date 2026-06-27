# Gemma4 + Claude Code - Guide Rapide

**Modèle confirmé : `gemma4:latest` (9.6 GB, déjà téléchargé)**

---

## ⚡ Démarrage en 3 commandes

### 1. Vérifie que Ollama tourne
```bash
curl http://localhost:11434/api/tags
# ✅ Expected: JSON avec la liste des modèles incluant gemma4
```

### 2. Vérifier gemma4 dans la liste
```bash
ollama list | findstr gemma4
# ✅ Expected: gemma4:latest  c6eb396dbd59  9.6 GB  2 weeks ago
```

### 3. Lancer Claude Code avec gemma4
```bash
# Option A: Via le script (recommandé)
cd C:\Users\Administrator\Documents\twisterlab
.\start-claude-code-local.bat

# Option B: En ligne de commande directe
loclaude start ^
  --model gemma4:latest ^
  --mcp-server twisterlab http://192.168.0.30:30393/mcp ^
  --directory C:\Users\Administrator\Documents\twisterlab
```

---

## 📋 Commandes courantes avec gemma4

| Cas d'usage | Commande |
|-----------|----------|
| **Lancer Claude Code** | `loclaude start --model gemma4:latest --directory .` |
| **Tester gemma4 seul** | `ollama run gemma4:latest "Hello, explain yourself"` |
| **Voir les infos du modèle** | `ollama show gemma4:latest` |
| **Basculer vers qwen2.5-coder** | `loclaude start --model qwen2.5-coder:7b --directory .` |
| **Basculer vers deepseek-r1** | `loclaude start --model deepseek-r1:latest --directory .` |

---

## ✅ Vérifications

**Gemma4 est présent :**
```bash
ollama list | findstr gemma4
```
✅ Résultat attendu : `gemma4:latest  c6eb396dbd59  9.6 GB  2 weeks ago`

**Ollama fonctionne :**
```bash
curl -s http://localhost:11434/api/tags | findstr model
```
✅ Résultat attendu : JSON avec `gemma4` dedans

**loclaude est installé :**
```bash
loclaude --version
```
✅ Résultat attendu : `loclaude/0.0.5`

---

## 🎯 Cas d'usage : Claude Code + Gemma4

### Pour explorer du code
```bash
loclaude start \
  --model gemma4:latest \
  --directory C:\Users\Administrator\Documents\twisterlab
  
# Dans Claude Code, tape:
# "Explore src/twisterlab and explain the architecture"
```

### Pour écrire/modifier du code
```bash
loclaude start \
  --model gemma4:latest \
  --directory C:\Users\Administrator\Documents\twisterlab
  
# Dans Claude Code, tape:
# "Create a new audit logger test file in tests/"
```

### Pour déboguer
```bash
loclaude start \
  --model gemma4:latest \
  --mcp-server twisterlab http://192.168.0.30:30393/mcp \
  --directory C:\Users\Administrator\Documents\twisterlab
  
# Dans Claude Code, tape:
# "Use the MCP tools to check system health"
```

---

## 🚀 Premier lancement

1. **Ouvre PowerShell/Terminal dans le dossier TwisterLab**
   ```bash
   cd C:\Users\Administrator\Documents\twisterlab
   ```

2. **Lance le script**
   ```bash
   .\start-claude-code-local.bat
   ```

3. **Vois la sortie**
   ```
   [1/3] Checking Ollama...
   ✓ Ollama is running
   [2/3] Checking Ollama models...
   ✓ gemma4:latest is available
   [3/3] Checking MCP Server TwisterLab...
   ✓ MCP TwisterLab is accessible
   
   Configuration Summary:
   ==========================================
   Model: gemma4:latest
   Ollama: http://localhost:11434
   MCP Server: http://192.168.0.30:30393/mcp
   Directory: C:\Users\Administrator\Documents\twisterlab
   ==========================================
   
   Starting loclaude with Claude Code...
   ```

4. **Claude Code démarre** — tu peux maintenant interagir avec lui en ligne de commande

---

## 💡 Notes

- **Gemma4 a été téléchargé il y a 2 semaines** → prêt à l'emploi
- **Taille : 9.6 GB** → parfait pour une RTX 3060
- **VRAM utilisée** : ~8-9 GB pendant l'inférence
- **Temps de première réponse** : 3-5 secondes (le modèle se charge)
- **Temps de réponse normal** : 1-3 secondes

---

## ❓ Dépannage rapide

**Erreur : "gemma4 not found"**
```bash
ollama pull gemma4:latest
```

**Erreur : "Ollama not running"**
```bash
# Terminal séparé:
ollama serve
```

**Erreur : "loclaude command not found"**
```bash
npm install -g loclaude
```

**Claude Code démarre mais lentement**
→ Normal, le modèle gemma4 se charge. Première réponse : 5-10 secondes.

---

## 🎉 Tu es prêt !

```bash
cd C:\Users\Administrator\Documents\twisterlab
.\start-claude-code-local.bat
```

**Utilise Claude Code local avec gemma4 pour explorer et modifier le code TwisterLab.**

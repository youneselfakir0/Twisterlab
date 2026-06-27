# Claude Code Local + TwisterLab MCP - Configuration Complète

**Configuration active : `gemma4:latest` (Ollama)**

## 📋 Fichiers créés

```
C:\Users\Administrator\Documents\twisterlab\
├── start-claude-code-local.bat         ← 🚀 LANCER ICI (script de démarrage)
├── LOCLAUDE_SETUP_GUIDE.md             ← 📖 Guide détaillé (116 lignes)
└── MCP_SETUP_STATUS.md                 ← 📊 Status MCP (voir info ci-dessous)
```

---

## ✅ STATUS ACTUEL

### Logiciels installés
- ✅ **npm** v11.11.0 (vérifiée)
- ✅ **loclaude** v0.0.5 (installée globalement)
- ✅ **Ollama** (doit tourner avant de lancer Claude Code)

### MCP Server TwisterLab
- ✅ **URL:** http://192.168.0.30:30393/mcp
- ✅ **Status:** Connected
- ✅ **Tools:** 33 disponibles
- ✅ **Enregistré:** Dans Claude Code

### Modèles Ollama disponibles (en ordre de priorité)
- **gemma4:latest** (recommandé, 9.6 GB, parfait pour Claude Code)
- **qwen2.5-coder:7b** (rapide, 4.7 GB)
- **deepseek-r1:latest** (excellent reasoning, lent)

---

## 🚀 DÉMARRAGE RAPIDE (3 étapes)

### Étape 1: Démarrer Ollama
```bash
# Terminal 1 - LAISSE OUVERT
ollama serve
```

### Étape 2: Vérifier un modèle
```bash
# Terminal 2
ollama list
# Doit afficher: qwen2.5-coder:7b ou deepseek-r1:latest
```

### Étape 3: Lancer Claude Code Local
```bash
# Terminal 2
cd C:\Users\Administrator\Documents\twisterlab
.\start-claude-code-local.bat

# Ou sans le script (manuel):
loclaude start `
  --model gemma4:latest `
  --mcp-server twisterlab http://192.168.0.30:30393/mcp `
  --directory .
```

**C'est tout!** Claude Code local est maintenant actif. 🎉

---

## 📚 DOCUMENTATION

### Pour les détails complets:
👉 **[LOCLAUDE_SETUP_GUIDE.md](./LOCLAUDE_SETUP_GUIDE.md)** (5 minutes de lecture)

Couvre:
- Vue d'ensemble du système
- Étapes détaillées avec outputs attendus
- Utilisation et exemples
- Outils disponibles (33 MCP + outils natifs)
- Dépannage
- Raccourcis clavier

### Pour le status MCP:
👉 **[MCP_SETUP_STATUS.md](./MCP_SETUP_STATUS.md)** (diagnostics)

Contient:
- Vérification MCP TwisterLab (✅ Connected)
- Blocages et solutions (API key vs VS Code vs loclaude)
- Résumé de configuration

---

## 🎯 CE QUI FONCTIONNE MAINTENANT

### Outils natifs Claude Code
- ✅ Bash (exécuter des commandes)
- ✅ Read (lire des fichiers)
- ✅ Edit (modifier des fichiers)
- ✅ Grep (chercher du texte)
- ✅ Glob (lister des fichiers)

### 33 outils MCP TwisterLab
- ✅ monitoring_health_check
- ✅ monitoring_get_system_metrics
- ✅ monitoring_list_containers
- ✅ monitoring_get_container_logs
- ✅ Et 29 autres...

### Modèles Ollama
- ✅ gemma4:latest (recommandé — 9.6 GB, parfait pour Claude Code)
- ✅ qwen2.5-coder:7b (rapide, code)
- ✅ deepseek-r1:latest (reasoning, lent)

---

## ⚡ PROCHAINES ÉTAPES

### Immédiatement:
1. Ouvre `LOCLAUDE_SETUP_GUIDE.md`
2. Suis les 3 étapes de démarrage
3. Tape une commande dans Claude Code

### Exemple première commande:
```
Explore the /src directory and tell me what TwisterLab does
```

Claude utilisera les outils MCP pour explorer le code automatiquement.

---

## 🔍 VÉRIFICATION RAPIDE

Pour vérifier que tout est en place:

```bash
# Terminal (PowerShell):
cd C:\Users\Administrator\Documents\twisterlab

# 1. Vérifier npm
npm --version
# ✅ Expected: v11.11.0

# 2. Vérifier loclaude
loclaude --version
# ✅ Expected: loclaude/0.0.5

# 3. Vérifier Ollama (doitcommuniquer)
curl http://localhost:11434/api/tags
# ✅ Expected: JSON avec les modèles

# 4. Vérifier MCP TwisterLab
curl http://192.168.0.30:30393/tools
# ✅ Expected: JSON avec les 33 tools (ou error si réseau bloqué, c'est OK)
```

---

## 📝 NOTES

- **Ollama doit tourner avant Claude Code** — c'est le serveur LLM
- **Première réponse peut être lente** — le modèle se charge en mémoire VRAM
- **MCP TwisterLab est optionnel** — Claude Code fonctionne aussi sans (juste moins d'outils)
- **100% gratuit et local** — aucune donnée envoyée au cloud
- **RTX 3060 compatible** — qwen2.5-coder utilise ~5 GB VRAM

---

## 💡 TIPS

**Pour basculer entre modèles rapidement:**
```bash
# Avec deepseek-r1 au lieu de gemma4
loclaude start `
  --model deepseek-r1:latest `
  --mcp-server twisterlab http://192.168.0.30:30393/mcp `
  --directory .

# Ou avec qwen2.5-coder
loclaude start `
  --model qwen2.5-coder:7b `
  --mcp-server twisterlab http://192.168.0.30:30393/mcp `
  --directory .
```

**Pour exécuter une commande unique puis quitter:**
```bash
loclaude --input "Explore TwisterLab /src directory"
```

**Pour voir les logs détaillés:**
```bash
loclaude start --verbose
```

---

## ❓ FAQ

**Q: Qu'est-ce qui se passe si Ollama n'est pas en train de tourner?**
A: Le script détectera l'erreur et te demandera de démarrer Ollama d'abord.

**Q: Qu'est-ce qui se passe si je n'ai pas de modèle téléchargé?**
A: Le script détectera et te montrera comment en télécharger un (ollama pull qwen2.5-coder).

**Q: Qu'est-ce qui se passe si le MCP TwisterLab n'est pas accessible?**
A: Claude Code fonctionnera quand même avec les outils natifs (Bash, Read, Edit). Le MCP ajoute juste des outils supplémentaires.

**Q: Combien ça coûte?**
A: Zéro. Complètement gratuit. Tout tourne en local sur ta RTX 3060.

**Q: Qu'est-ce qui est envoyé au cloud?**
A: Rien. Zéro. Tout fonctionne offline (sauf si tu essaies de faire du web search, mais tu ne le fais pas).

**Q: Quel modèle gemma4 recommandes-tu?**
A: `gemma4:latest` — c'est la version complète (9.6 GB) et elle est déjà téléchargée chez toi. Parfait pour Claude Code.

---

## 🎉 TU ES PRÊT!

Ouvre `start-claude-code-local.bat` et profite de Claude Code local avec tous les outils TwisterLab.

**Questions?** Regarde d'abord `LOCLAUDE_SETUP_GUIDE.md` → section "Dépannage".

**Besoin d'aide?** Dis-moi à quelle étape tu es bloqué.

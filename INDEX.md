# 📑 INDEX - Claude Code Local + TwisterLab MCP

## 🎯 PAR OÙ COMMENCER?

### Si tu es pressé (30 sec):
→ **[QUICKSTART.txt](./QUICKSTART.txt)** — Les 3 lignes de commande

### Si tu veux comprendre (5 min):
→ **[CLAUDE_CODE_LOCAL_README.md](./CLAUDE_CODE_LOCAL_README.md)** — Vue d'ensemble rapide

### Si tu veux les détails (15 min):
→ **[LOCLAUDE_SETUP_GUIDE.md](./LOCLAUDE_SETUP_GUIDE.md)** — Guide complet avec troubleshooting

### Si tu as des problèmes:
→ **[MCP_SETUP_STATUS.md](./MCP_SETUP_STATUS.md)** — Diagnostics et options alternatives

---

## 📋 FICHIERS CRÉÉS POUR CETTE CONFIGURATION

### 🚀 Démarrage
```
start-claude-code-local.bat         ← Double-cliquer pour lancer Claude Code
QUICKSTART.txt                      ← Les 3 commandes essentielles (30 sec de lecture)
```

### 📖 Documentation
```
CLAUDE_CODE_LOCAL_README.md         ← Vue d'ensemble (3 min)
LOCLAUDE_SETUP_GUIDE.md             ← Guide détaillé (5 min)
SETUP_COMPLETE.md                   ← Checklist pré-démarrage
MCP_SETUP_STATUS.md                 ← Diagnostics MCP
```

### 🛠️ Skills Claude Code
```
.claude/skills/twisterlab-tools/
├── SKILL.md                        ← Skill officiel Claude Code
├── twisterlab_tools.py             ← Client HTTP asyncio
├── ollama_integration.py           ← Intégration Ollama
├── requirements.txt                ← Dépendances Python
└── README.md                       ← Guide usage du skill
```

---

## 🚀 DÉMARRER MAINTENANT

### Étape 1: Terminal Ollama
```powershell
ollama serve
```

### Étape 2: Terminal Claude Code
```powershell
cd C:\Users\Administrator\Documents\twisterlab
.\start-claude-code-local.bat
```

### Étape 3: Utiliser Claude Code
```
> Explore TwisterLab /src and explain the architecture
```

---

## ✅ CE QUI EST INCLUS

| Composant | Status | Details |
|-----------|--------|---------|
| **npm** | ✅ Installé | v11.11.0 |
| **loclaude** | ✅ Installé | v0.0.5 (Claude Code bridge) |
| **MCP TwisterLab** | ✅ Connecté | 33 outils, http://192.168.0.30:30393/mcp |
| **Claude Code** | ✅ Configuré | Via loclaude + Ollama |
| **Outils natifs** | ✅ Disponibles | Bash, Read, Edit, Grep, Glob |
| **Modèles Ollama** | ⏳ À toi de choisir | qwen2.5-coder:7b ou deepseek-r1 |

---

## 💡 TIPS RAPIDES

**Pour basculer de modèle:**
```powershell
loclaude start --model deepseek-r1:latest --mcp-server twisterlab http://192.168.0.30:30393/mcp --directory .
```

**Pour une commande unique:**
```powershell
loclaude --input "Explore TwisterLab" --model qwen2.5-coder:7b
```

**Pour voir les logs détaillés:**
```powershell
loclaude start --verbose
```

---

## ❓ FAQ ULTRA-RAPIDE

**Q: Ça coûte combien?**
A: Gratuit. 100% local, zéro coûts API.

**Q: Qu'est-ce qui est envoyé au cloud?**
A: Rien. Tout tourne offline sur ta machine.

**Q: Pourquoi mon Claude Code est lent?**
A: Probable: Le modèle est gros. Basculer vers qwen2.5-coder (plus rapide).

**Q: Qu'est-ce qui se passe si Ollama plante?**
A: Claude Code arrête. Relance Ollama avec `ollama serve`.

**Q: Où sont les logs?**
A: Terminal où tu as lancé `start-claude-code-local.bat`.

---

## 🔗 CHAÎNE DE LECTURE RECOMMANDÉE

1. **Ce fichier (2 min)** ← Tu es ici
2. **[QUICKSTART.txt](./QUICKSTART.txt)** (30 sec) — Les 3 commandes
3. **[CLAUDE_CODE_LOCAL_README.md](./CLAUDE_CODE_LOCAL_README.md)** (3 min) — Vérifications rapides
4. **[LOCLAUDE_SETUP_GUIDE.md](./LOCLAUDE_SETUP_GUIDE.md)** (5 min) — Guide complet
5. **Lancer `start-claude-code-local.bat`** ← Profiter! 🎉

---

## 📞 SUPPORT

**Si tu es bloqué à l'étape 1 ou 2:**
→ Voir dépannage dans [LOCLAUDE_SETUP_GUIDE.md](./LOCLAUDE_SETUP_GUIDE.md#-dépannage)

**Si tu veux les options alternatives (API cloud, VS Code Extension):**
→ Voir [MCP_SETUP_STATUS.md](./MCP_SETUP_STATUS.md)

**Si tu veux les détails techniques du MCP:**
→ Voir [.claude/skills/twisterlab-tools/SKILL.md](./.claude/skills/twisterlab-tools/SKILL.md)

---

## 🎉 TU ES PRÊT!

Ouvre [QUICKSTART.txt](./QUICKSTART.txt) et lance `start-claude-code-local.bat`.

Enjoy Claude Code local! 🚀

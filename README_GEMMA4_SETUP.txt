📌 INDEX - Claude Code + Gemma4 Configuration

============================================
🚀 DÉMARRER IMMÉDIATEMENT
============================================

Option A (Recommandée) :
  cd C:\Users\Administrator\Documents\twisterlab
  .\start-claude-code-local.bat

Option B (PowerShell intelligent) :
  .\GEMMA4_LAUNCH.ps1

Option C (Une ligne) :
  loclaude start --model gemma4:latest --directory .

⚠️  PRÉREQUIS: Ollama doit tourner avant!
  ollama serve    (terminal séparé)

============================================
📚 OÙ CHERCHER L'INFO
============================================

❓ Je veux lancer Claude Code rapidement
  → Lis: GEMMA4_FINAL_SETUP.md (5 min)

❓ Je veux apprendre à utiliser Gemma4
  → Lis: GEMMA4_SETUP.md (10 min)

❓ Je veux la configuration complète
  → Lis: CLAUDE_CODE_LOCAL_README.md (15 min)

❓ Je veux tous les détails techniques
  → Lis: LOCLAUDE_SETUP_GUIDE.md (20 min)

❓ Je veux résumer ce qui a été changé
  → Lis: GEMMA4_ACTIVATED.md (5 min)

❓ Je veux des commandes sans explications
  → Lis: GEMMA4_QUICK_LAUNCH.sh (copy/paste)

============================================
📋 FICHIERS CLÉS MODIFIÉS
============================================

✅ start-claude-code-local.bat
   Modification: Priorité gemma4 → qwen → deepseek
   Action: Lance le script d'une ligne

✅ CLAUDE_CODE_LOCAL_README.md
   Modification: Modèle par défaut = gemma4:latest
   Action: Documentation mise à jour

✅ GEMMA4_SETUP.md
   Nouveau fichier
   Action: Guide dédié + exemples

✅ GEMMA4_LAUNCHED.ps1
   Nouveau fichier
   Action: Launcher PowerShell intelligent

============================================
🎯 MODÈLE CONFIGURÉ
============================================

Modèle principal:      gemma4:latest ✅
Taille:                9.6 GB
État téléchargement:   ✅ Prêt
ID:                    c6eb396dbd59

Fallback #1:           qwen2.5-coder:7b
Fallback #2:           deepseek-r1:latest
JAMAIS:                qwen3.5 (tu n'en as pas)

============================================
✅ PRÉREQUIS VÉRIFIÉs
============================================

✅ npm:               v11.11.0 ✓
✅ loclaude:          v0.0.5 ✓
✅ Ollama:            Doit tourner avant
✅ gemma4:latest:     c6eb396dbd59 ✓
✅ MCP TwisterLab:    Optionnel (33 outils)

============================================
⚡ COMMANDES COURANTES
============================================

Tester le modèle gemma4 directement:
  ollama run gemma4:latest "Hello"

Voir tous les modèles disponibles:
  ollama list

Lancer Claude Code sans MCP:
  loclaude start --model gemma4:latest --directory .

Lancer Claude Code avec MCP:
  loclaude start \
    --model gemma4:latest \
    --mcp-server twisterlab http://192.168.0.30:30393/mcp \
    --directory .

Basculer vers qwen2.5-coder:
  loclaude start --model qwen2.5-coder:7b --directory .

Basculer vers deepseek-r1:
  loclaude start --model deepseek-r1:latest --directory .

============================================
💡 NOTES IMPORTANTES
============================================

• Ollama DOIT tourner avant Claude Code
  Commande: ollama serve (terminal séparé)

• Première réponse sera lente (3-5s)
  Ensuite: 1-3 secondes (normal)

• Gemma4 utilise ~8-9 GB VRAM sur RTX 3060
  Disponible dans ta machine? Vérifier avant

• MCP TwisterLab est optionnel
  Sans: Claude Code fonctionne normalement
  Avec: +33 outils pour monitoring/system

• Zéro frais, 100% local
  Aucune donnée envoyée au cloud

============================================
🎉 TU ES PRÊT
============================================

Lancer:
  cd C:\Users\Administrator\Documents\twisterlab
  .\start-claude-code-local.bat

Puis taper:
  "Explore TwisterLab src/"
  "Explain the architecture"
  "Create a test file"
  etc.

Claude Code + Gemma4 prêts à l'emploi! 🚀

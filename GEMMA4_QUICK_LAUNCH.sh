# Lancer Claude Code + Gemma4 en une ligne

# ============================================
# OPTION 1 : Via le script (recommandé)
# ============================================
# PowerShell:
cd C:\Users\Administrator\Documents\twisterlab; .\start-claude-code-local.bat

# ============================================
# OPTION 2 : Commande directe (sans MCP)
# ============================================
loclaude start --model gemma4:latest --directory C:\Users\Administrator\Documents\twisterlab

# ============================================
# OPTION 3 : Avec MCP TwisterLab (full)
# ============================================
loclaude start `
  --model gemma4:latest `
  --mcp-server twisterlab http://192.168.0.30:30393/mcp `
  --directory C:\Users\Administrator\Documents\twisterlab

# ============================================
# PRÉREQUIS :
# ============================================
# 1. Ollama doit tourner dans un terminal séparé:
ollama serve

# 2. Vérifier que gemma4 existe:
ollama list | findstr gemma4
# ✅ Expected: gemma4:latest  c6eb396dbd59  9.6 GB

# 3. loclaude doit être installé:
loclaude --version
# ✅ Expected: loclaude/0.0.5

# ============================================
# APRÈS LANCEMENT :
# ============================================
# Tu peux taper des commandes comme:
# - "Explore TwisterLab src/"
# - "Create a test file"
# - "Explain the architecture"
# - etc.

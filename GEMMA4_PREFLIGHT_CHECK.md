# ✅ Claude Code + Gemma4 - Checklist Prélancement

**Avant de lancer, vérifie ceci :**

---

## ✓ Checklist Complète (3 minutes)

### 1️⃣ Ollama tourne
```bash
# Dans PowerShell/Terminal:
curl -s http://localhost:11434/api/tags | findstr model
```
**✅ Attendu:** Réponse JSON avec les modèles  
**❌ Si erreur:** Lance `ollama serve` dans un terminal séparé

---

### 2️⃣ Gemma4 est présent
```bash
ollama list | findstr gemma4
```
**✅ Attendu:**
```
gemma4:latest       c6eb396dbd59    9.6 GB    2 weeks ago
```

**❌ Si absent:** Télécharge-le
```bash
ollama pull gemma4:latest
```

---

### 3️⃣ loclaude est installé
```bash
loclaude --version
```
**✅ Attendu:** `loclaude/0.0.5`  
**❌ Si absent:**
```bash
npm install -g loclaude
```

---

### 4️⃣ Tu es dans le bon répertoire
```bash
cd C:\Users\Administrator\Documents\twisterlab
pwd  # ou "cd" tout seul
```
**✅ Attendu:** `C:\Users\Administrator\Documents\twisterlab`

---

### 5️⃣ Le script existe
```bash
ls *.bat | findstr start-claude
# ou
Test-Path "start-claude-code-local.bat"
```
**✅ Attendu:** `True` ou voir le fichier listré  
**❌ Si absent:** Télécharge le dépôt TwisterLab

---

## 🚀 Si tout est ✅ : LANCER

```bash
.\start-claude-code-local.bat
```

Attends que tu vois :
```
Starting loclaude with Claude Code...

Configuration Summary:
==========================================
Model: gemma4:latest
Ollama: http://localhost:11434
MCP Server: http://192.168.0.30:30393/mcp
Directory: C:\Users\Administrator\Documents\twisterlab
==========================================
```

Puis Claude Code démarre.

---

## ❌ Si une étape échoue

| Étape | Erreur | Solution |
|-------|--------|----------|
| 1 | Ollama ne répond pas | `ollama serve` (terminal séparé) |
| 2 | gemma4 absent | `ollama pull gemma4:latest` (attends 5+ min) |
| 3 | loclaude absent | `npm install -g loclaude` (attends 1 min) |
| 4 | Mauvais dossier | `cd C:\Users\Administrator\Documents\twisterlab` |
| 5 | Script manquant | Clone/télécharge le dépôt TwisterLab |

---

## 💾 Vérification rapide (une ligne)

```bash
(curl -s http://localhost:11434/api/tags) -and (ollama list | findstr gemma4) -and (loclaude --version)
```

**✅ Si 0 erreurs:** Tu es prêt

---

## 📊 Ressources minimum

| Ressource | Minimum | Idéal |
|-----------|---------|-------|
| RAM | 16 GB | 32 GB |
| VRAM | 8 GB | 12+ GB |
| Disque libre | 20 GB | 50+ GB |
| Gemma4 requiert | ~9 GB | ✓ disponible |

**Check ta RTX 3060 :**
```bash
nvidia-smi
# Vérifier que VRAM > 10 GB disponible
```

---

## 🎯 Les 3 étapes finales

1. **Assure-toi que Ollama tourne** ← CRITIQUE
   ```bash
   ollama serve
   ```

2. **Vérifie gemma4 existe**
   ```bash
   ollama list | findstr gemma4
   ```

3. **Lance Claude Code**
   ```bash
   cd C:\Users\Administrator\Documents\twisterlab
   .\start-claude-code-local.bat
   ```

---

## 📝 Notes

- 🟢 **Vert = go**
- 🟡 **Jaune = attention**
- 🔴 **Rouge = bloqué, fix avant**

---

## 🆘 Si tu es bloqué

Dis-moi à quelle étape et l'erreur exacte. Ex:

> "À l'étape 2, j'ai : 'curl: command not found'"

Ou :

> "À l'étape 1, ollama list montre 0 modèles"

Je fix rapidement.

---

✅ **Prêt à lancer!**

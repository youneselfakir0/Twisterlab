# Claude Code + TwisterLab - Guide d'utilisation

**Prérequis :** Ollama tourne avec `ollama serve` (terminal séparé)

---

## 🚀 Lancer Claude Code pour TwisterLab

```bash
cd C:\Users\Administrator\Documents\twisterlab
.\claude-code-twisterlab.bat
```

Tu verras :
```
============================================================
Claude Code + TwisterLab Setup
============================================================

Repository: C:\Users\Administrator\Documents\twisterlab
Model: gemma4:latest (Ollama)

Use these commands in Claude Code:
  - "Explore src/twisterlab structure"
  - "What does the API do?"
  - "Show me the database models"
  - "Fix the audit logger integration"
  - "Run the tests"

Type 'exit' or Ctrl+C to quit Claude Code
============================================================
```

Puis tu verras le prompt :
```
>
```

---

## 💬 Exemples de commandes à taper

### Exploration
```
> Explore src/twisterlab structure and explain the main directories
```

```
> List all Python files in src/twisterlab/api/routes/
```

```
> Show me the database connection code in src/twisterlab/database/
```

### Analyse
```
> What is the purpose of the Maestro agent?
```

```
> Explain how the audit logging system works
```

```
> Compare the three main database models (Agent, Resilience, Learning)
```

### Modification
```
> Create a new test file for the audit logger in tests/unit/
```

```
> Add docstrings to all functions in src/twisterlab/services/audit_logger.py
```

```
> Fix the ImportError in src/twisterlab/api/main.py
```

### Debugging
```
> Find all TODO comments in the codebase
```

```
> Search for functions that use asyncio but aren't marked async
```

```
> Show me the error handling pattern used in routes/
```

### Tâches spécifiques
```
> Integrate the Run Audit System into POST /domain/sync
```

```
> Create a health check endpoint for the audit logger
```

```
> Write a test for the AuditLoggerServiceImpl class
```

---

## 🛠 Outils disponibles dans Claude Code

### Outils natifs (toujours disponibles)
- **Read** : Lire des fichiers (`cat`, `head`, `tail`)
- **Edit** : Modifier des fichiers (ajouter, remplacer des lignes)
- **Bash** : Exécuter des commandes shell
- **Glob** : Lister des fichiers avec patterns
- **Grep** : Chercher du texte dans les fichiers

### Outils MCP TwisterLab (optionnel)
- monitoring_health_check
- monitoring_get_system_metrics
- monitoring_list_containers
- database_execute_query
- Et 28 autres...

---

## 📝 Bonnes pratiques

### ✅ À faire
- Taper des commandes en français ou anglais
- Être spécifique : "Show me line 10-20 of main.py"
- Demander à Claude d'explorer avant de modifier
- Laisser Claude poser des questions
- Vérifier les changements avant de les appliquer

### ❌ À ne pas faire
- Modifier des fichiers sans les lire d'abord
- Demander des changements vagues ("fix everything")
- Oublier que Claude Code a accès au disque local
- Essayer de lancer des commandes Windows natives (utiliser `bash` ou PowerShell)

---

## 🔄 Workflow typique

1. **Lance Claude Code**
   ```bash
   .\claude-code-twisterlab.bat
   ```

2. **Explore le code**
   ```
   > Explore src/twisterlab and tell me the main components
   ```

3. **Trouve ce que tu cherches**
   ```
   > Show me the audit logger implementation
   ```

4. **Demande des modifications**
   ```
   > Add error handling to the log_end method in audit_logger.py
   ```

5. **Vérifie les résultats**
   ```
   > Run tests/unit/test_audit_logger.py
   ```

6. **Quitte**
   ```
   > exit
   ```

---

## 🆘 Troubleshooting

| Problème | Solution |
|----------|----------|
| `Ollama not running` | Lance `ollama serve` dans un terminal séparé |
| Claude Code quitte immédiatement | Vérifier que Ollama tourne |
| Commandes n'existent pas | Utiliser `Bash` ou `Read` plutôt que les commandes directes |
| Fichiers non trouvés | Utiliser des chemins absolus à partir de `C:\Users\Administrator\Documents\twisterlab` |
| Erreur de permissions | Certains fichiers peuvent être en lecture seule |

---

## 📚 Ressources

- **Prompt système** : Voir `CLAUDE_CODE_SYSTEM_PROMPT.md`
- **Architecture** : Voir `docs/architecture/`
- **API** : Voir `src/twisterlab/api/`
- **Database** : Voir `src/twisterlab/database/`
- **Agents** : Voir `src/twisterlab/agents/`

---

**Tu es prêt ! Lance Claude Code et commence à explorer TwisterLab.** 🚀

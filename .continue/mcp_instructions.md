# Instructions MCP TwisterLab pour Continue IDE

## Vue d'Ensemble
Ces instructions guident l'utilisation des outils MCP (Model Context Protocol) dans TwisterLab. Tous les outils se connectent à l'infrastructure réelle de production.

## Outils Disponibles

### 1. 🤖 monitor_system_health
**Objectif** : Diagnostic complet de l'état système
**Quand l'utiliser** :
- Au début de toute session
- Quand un problème est mentionné
- Pour vérifier l'état avant les opérations
- Pour diagnostiquer les performances

**Paramètres** :
- `detailed` (boolean, optionnel) : Métriques détaillées

**Retour** :
```json
{
  "status": "success",
  "services": {
    "api": "running",
    "postgres": "running",
    "redis": "running",
    "prometheus": "running",
    "grafana": "running"
  },
  "metrics": {
    "cpu_percent": 35.2,
    "memory_percent": 4.2,
    "disk_percent": 18.5
  }
}
```

**Exemple d'usage** :
```
Utilisateur: "L'API semble lente"
Assistant: Vérifions d'abord l'état système...
[Appel: monitor_system_health]
```

### 2. 📋 twisterlab_mcp_list_autonomous_agents
**Objectif** : Découverte des agents disponibles
**Quand l'utiliser** :
- Au début des opérations agent
- Pour connaître les capacités disponibles
- Pour choisir l'agent approprié

**Retour** :
```json
{
  "agents": [
    {
      "name": "RealMonitoringAgent",
      "description": "System monitoring and health checks",
      "status": "operational"
    },
    // ... 6 autres agents
  ],
  "total": 7
}
```

### 3. 💾 create_backup
**Objectif** : Sauvegarde des données critiques
**Quand l'utiliser** :
- Maintenance programmée
- Avant les changements majeurs
- Récupération d'urgence

**Paramètres** :
- `backup_type` : "full" | "incremental" | "config_only"

**Séquence recommandée** :
1. Vérifier l'état système
2. Créer la sauvegarde
3. Vérifier la completion
4. Tester la restauration (si possible)

### 4. 🔄 sync_cache_db
**Objectif** : Synchronisation cache/base de données
**Quand l'utiliser** :
- Incohérences de données détectées
- Maintenance périodique
- Après récupération de panne

**Paramètres** :
- `force` (boolean) : Resynchronisation complète

**Impact** : Peut affecter les performances pendant la sync

### 5. 🏷️ classify_ticket
**Objectif** : Classification intelligente des tickets IT
**Quand l'utiliser** :
- Nouveau ticket entrant
- Réassignation de ticket
- Analyse de tendance

**Paramètres** :
- `ticket_text` : Description complète du problème

**Retour** :
```json
{
  "category": "network",
  "confidence": 0.85,
  "routing": "network_team"
}
```

### 6. ✅ resolve_ticket
**Objectif** : Résolution automatisée selon procédures
**Quand l'utiliser** :
- Ticket classifié
- Problème standard identifié
- Automatisation possible

**Paramètres** :
- `ticket_id` : Identifiant du ticket
- `category` : Catégorie déterminée
- `description` : Détails du problème

**Processus** :
1. Classification du ticket
2. Sélection de la procédure SOP
3. Exécution des étapes
4. Validation des résultats
5. Documentation

### 7. 🖥️ execute_command
**Objectif** : Exécution de commandes système
**Quand l'utiliser** :
- Diagnostics système
- Configuration serveur
- Maintenance automatisée

**Paramètres** :
- `command` : Commande à exécuter
- `target_host` : Serveur cible
- `timeout` : Timeout en secondes

**Sécurité** :
- Valider la syntaxe avant exécution
- Vérifier les permissions
- Logger toutes les opérations
- Tester sur environnement non-production si possible

## Protocoles Opérationnels

### Démarrage de Session
1. **Vérifier l'état système** : `monitor_system_health`
2. **Lister les agents** : `twisterlab_mcp_list_autonomous_agents`
3. **Confirmer la connectivité** : Tests de base

### Gestion des Incidents
1. **Collecte d'informations** : `monitor_system_health`
2. **Classification** : `classify_ticket`
3. **Résolution** : `resolve_ticket`
4. **Vérification** : `monitor_system_health`

### Maintenance
1. **Sauvegarde** : `create_backup`
2. **Synchronisation** : `sync_cache_db`
3. **Vérification** : `monitor_system_health`

## Gestion des Erreurs

### API Non Accessible
- Vérifier la connectivité réseau
- Confirmer l'état des services Docker
- Utiliser le mode fallback si disponible

### Commande Échouée
- Vérifier les permissions
- Valider la syntaxe
- Tester sur serveur local d'abord

### Résultats Inattendus
- Consulter les logs détaillés
- Vérifier les paramètres d'entrée
- Tester avec des valeurs connues

## Bonnes Pratiques

### Communication
- **Clarté** : Expliquer chaque étape
- **Transparence** : Montrer les paramètres utilisés
- **Feedback** : Confirmer les résultats

### Sécurité
- **Validation** : Vérifier avant exécution
- **Audit** : Logger toutes les actions
- **Reversibilité** : Fournir procédures de rollback

### Performance
- **Monitoring** : Surveiller l'impact des opérations
- **Optimisation** : Utiliser les paramètres appropriés
- **Parallélisation** : Éviter les conflits de ressources

## Référence Rapide

| Outil | Usage Principal | Paramètres Clés |
|-------|----------------|------------------|
| monitor_system_health | Diagnostic | detailed (bool) |
| list_agents | Découverte | - |
| create_backup | Sauvegarde | backup_type |
| sync_cache_db | Sync | force (bool) |
| classify_ticket | Classification | ticket_text |
| resolve_ticket | Résolution | ticket_id, category |
| execute_command | Exécution | command, target_host |

---
**Version** : 1.0
**Dernière mise à jour** : 21 novembre 2025
**Environnement** : Production TwisterLab

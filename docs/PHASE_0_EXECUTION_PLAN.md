# 🎯 PHASE 0: PLAN D'EXÉCUTION IMMÉDIAT

**Date Début**: 4 Février 2026  
**Approche**: Progressive avec validation ROI  
**Status**: 🔴 EN COURS (50% complété aujourd'hui)

---

## 📋 CHECKLIST PHASE 0 - STABILISATION

### ✅ **Complété Aujourd'hui (4 Février)**

- [x] **Audit infrastructure complet** - 14 vérifications
- [x] **Disk cleanup critique** - 15GB libérés (85% → 74%)
- [x] **DiskPressure résolu** - Node taint removed
- [x] **100+ pods nettoyés** - Stale/evicted/failed supprimés
- [x] **K3s restart** - Cluster rafraîchi
- [x] **Documentation créée**:
  - [x] `INFRASTRUCTURE_AUDIT_2026-02-04.md`
  - [x] `MCP_REBUILD_GUIDE.md`
  - [x] `PLAN_INTERVENTION_COMPLETE_2026-02.md`
- [x] **Build MCP lancé** - En cours (35+ min)
- [x] **Monitoring tools** - `monitor_mcp_build.py` créé
- [x] **Workflow CI/CD** - `.github/workflows/build-mcp.yml` créé
- [x] **Git commits** - 3 commits pushés sur GitHub

**Progress: 50%**

---

## 🔴 À COMPLÉTER (Reste de Phase 0)

### **0.1 - Finaliser MCP Services** 🔴 CRITIQUE

**Status**: ⏱️ Build en cours (35+ min)

**Actions Restantes**:
```bash
# 1. Attendre fin build (check toutes les 5 min)
python scripts/monitor_mcp_build.py

# 2. Une fois terminé, import dans K3s
ssh twister@192.168.0.30 "
  sudo docker save twisterlab/mcp-unified:latest | \
  sudo k3s ctr images import -
"

# 3. Vérifier image importée
ssh twister@192.168.0.30 "sudo k3s crictl images | grep mcp"

# 4. Deploy MCP services
kubectl set image deployment/mcp-unified \
  mcp-unified=twisterlab/mcp-unified:latest -n twisterlab
  
kubectl set image deployment/mcp-unified \
  mcp-unified=twisterlab/mcp-unified:latest -n twisterlab-dev

kubectl scale deployment mcp-unified --replicas=1 -n twisterlab
kubectl scale deployment mcp-unified --replicas=1 -n twisterlab-dev

# 5. Vérifier deployment
kubectl get pods -n twisterlab,twisterlab-dev | grep mcp
kubectl logs -n twisterlab -l app=mcp-unified --tail=50

# 6. Test santé
curl http://192.168.0.30:30080/health
```

**Critère Succès**: MCP pods 1/1 Running, health check 200 OK

**Durée Estimée**: 0.5-1 jour (attente build + deployment)

---

### **0.2 - Configuration Rotation Logs** 🔴 CRITIQUE

**Problème**: `kern.log` peut revenir à 12GB  
**Solution**: Rotation agressive permanente

**Actions**:
```bash
# SSH vers EdgeServer
ssh twister@192.168.0.30

# 1. Configuration logrotate pour kern.log
sudo tee /etc/logrotate.d/kern-aggressive << 'EOF'
/var/log/kern.log {
    daily
    rotate 3
    maxsize 500M
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
}
EOF

# 2. Configuration pour autres logs système
sudo tee /etc/logrotate.d/syslog-aggressive << 'EOF'
/var/log/syslog
/var/log/messages
{
    daily
    rotate 3
    maxsize 500M
    compress
    delaycompress
    missingok
    notifempty
}
EOF

# 3. Journald limitation
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/size-limit.conf << 'EOF'
[Journal]
SystemMaxUse=500M
SystemKeepFree=2G
MaxFileSec=1day
MaxRetentionSec=3day
EOF

sudo systemctl restart systemd-journald

# 4. Test rotation immédiat
sudo logrotate -f /etc/logrotate.conf

# 5. Vérifier
sudo du -sh /var/log
sudo journalctl --disk-usage
```

**Critère Succès**: `/var/log` < 2GB stable, journald < 500MB

**Durée**: 0.5 jour

---

### **0.3 - Backup Automatique PostgreSQL** 🔴 CRITIQUE

**Problème**: Aucun backup actuel = risk data loss  
**Solution**: Backup quotidien automatique

**Actions**:
```bash
# SSH vers EdgeServer
ssh twister@192.168.0.30

# 1. Créer répertoire backups
sudo mkdir -p /var/backups/twisterlab/{postgres,redis,configs}
sudo chown twister:twister /var/backups/twisterlab -R

# 2. Script backup PostgreSQL
sudo tee /usr/local/bin/backup-twisterlab-postgres.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/twisterlab/postgres"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
RETENTION_DAYS=7

echo "[$(date)] Starting PostgreSQL backup..."

# Backup via kubectl exec
kubectl exec -n twisterlab postgres-0 -- \
  pg_dumpall -U postgres | \
  gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Vérifier backup créé
if [ -f "$BACKUP_DIR/postgres_$DATE.sql.gz" ]; then
    SIZE=$(du -h "$BACKUP_DIR/postgres_$DATE.sql.gz" | cut -f1)
    echo "[$(date)] Backup successful: postgres_$DATE.sql.gz ($SIZE)"
else
    echo "[$(date)] ERROR: Backup failed!" >&2
    exit 1
fi

# Cleanup old backups
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Old backups cleaned (retention: $RETENTION_DAYS days)"

# Log to syslog
logger -t twisterlab-backup "PostgreSQL backup completed: $SIZE"
EOF

sudo chmod +x /usr/local/bin/backup-twisterlab-postgres.sh

# 3. Script backup Redis
sudo tee /usr/local/bin/backup-twisterlab-redis.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/twisterlab/redis"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
REDIS_POD=$(kubectl get pods -n twisterlab -l app=redis -o jsonpath='{.items[0].metadata.name}')

echo "[$(date)] Starting Redis backup from pod: $REDIS_POD"

# Save RDB
kubectl exec -n twisterlab $REDIS_POD -- redis-cli SAVE

# Copy dump.rdb
kubectl exec -n twisterlab $REDIS_POD -- cat /data/dump.rdb > "$BACKUP_DIR/redis_$DATE.rdb"

SIZE=$(du -h "$BACKUP_DIR/redis_$DATE.rdb" | cut -f1)
echo "[$(date)] Redis backup successful: $SIZE"

# Cleanup old backups
find "$BACKUP_DIR" -name "redis_*.rdb" -mtime +7 -delete
logger -t twisterlab-backup "Redis backup completed: $SIZE"
EOF

sudo chmod +x /usr/local/bin/backup-twisterlab-redis.sh

# 4. Script backup configs K8s
sudo tee /usr/local/bin/backup-twisterlab-configs.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/twisterlab/configs"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

echo "[$(date)] Starting K8s configs backup..."

# Backup all K8s resources
kubectl get all,configmaps,secrets,pvc,ingress --all-namespaces -o yaml \
  > "$BACKUP_DIR/k8s-resources_$DATE.yaml"

gzip "$BACKUP_DIR/k8s-resources_$DATE.yaml"

SIZE=$(du -h "$BACKUP_DIR/k8s-resources_$DATE.yaml.gz" | cut -f1)
echo "[$(date)] K8s configs backup successful: $SIZE"

# Cleanup
find "$BACKUP_DIR" -name "k8s-resources_*.yaml.gz" -mtime +7 -delete
logger -t twisterlab-backup "K8s configs backup completed: $SIZE"
EOF

sudo chmod +x /usr/local/bin/backup-twisterlab-configs.sh

# 5. Cron jobs quotidiens
(sudo crontab -l 2>/dev/null; echo "# TwisterLab Backups") | sudo crontab -
(sudo crontab -l; echo "0 2 * * * /usr/local/bin/backup-twisterlab-postgres.sh >> /var/log/twisterlab-backup.log 2>&1") | sudo crontab -
(sudo crontab -l; echo "15 2 * * * /usr/local/bin/backup-twisterlab-redis.sh >> /var/log/twisterlab-backup.log 2>&1") | sudo crontab -
(sudo crontab -l; echo "30 2 * * * /usr/local/bin/backup-twisterlab-configs.sh >> /var/log/twisterlab-backup.log 2>&1") | sudo crontab -

# 6. Test backup immédiat
sudo /usr/local/bin/backup-twisterlab-postgres.sh
sudo /usr/local/bin/backup-twisterlab-redis.sh
sudo /usr/local/bin/backup-twisterlab-configs.sh

# 7. Vérifier backups créés
ls -lh /var/backups/twisterlab/postgres/
ls -lh /var/backups/twisterlab/redis/
ls -lh /var/backups/twisterlab/configs/
```

**Critère Succès**: 
- Backups quotidiens PostgreSQL, Redis, K8s configs
- Rotation 7 jours
- Test restore réussi

**Durée**: 1 jour

---

### **0.4 - Monitoring Disk Space Proactif** 🟡 IMPORTANT

**Objectif**: Alertes avant DiskPressure

**Actions**:
```bash
# SSH vers EdgeServer
ssh twister@192.168.0.30

# 1. Script monitoring disk
sudo tee /usr/local/bin/check-disk-space.sh << 'EOF'
#!/bin/bash

THRESHOLD=75
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
    MESSAGE="WARNING: Disk usage at ${USAGE}% (threshold: ${THRESHOLD}%)"
    echo "[$(date)] $MESSAGE"
    logger -p user.warning -t disk-monitor "$MESSAGE"
    
    # Log top disk consumers
    echo "Top 10 disk consumers:"
    du -sh /var/* 2>/dev/null | sort -h | tail -10
fi
EOF

sudo chmod +x /usr/local/bin/check-disk-space.sh

# 2. Cron hourly
echo "0 * * * * /usr/local/bin/check-disk-space.sh" | sudo crontab -

# 3. Prometheus metric (si temps)
# TODO: Exposer disk usage comme métrique Prometheus
```

**Critère Succès**: Alertes si disk > 75%

**Durée**: 0.5 jour

---

## 📊 CRITÈRES DE VALIDATION PHASE 0

### **✅ Phase 0 Terminée Quand:**

1. ✅ **MCP Services**: 3/3 deployments Running (default, twisterlab, twisterlab-dev)
2. ✅ **Disk Space**: Stable < 70%, rotation configurée
3. ✅ **Backups**: Quotidiens automatiques PostgreSQL + Redis + K8s
4. ✅ **Monitoring**: Alertes disk space actives
5. ✅ **Documentation**: Guides à jour et testés
6. ✅ **Infrastructure Audit**: Score ≥ 75/100

### **📈 KPIs Phase 0**:

| Métrique | Avant | Cible | Actuel |
|----------|-------|-------|--------|
| **MCP Pods Running** | 0/3 | 3/3 | 0/3 ⏱️ |
| **Disk Usage** | 85% | <70% | 74% ✅ |
| **Backups/jour** | 0 | 3 | 0 ❌ |
| **DiskPressure Events** | Fréquent | 0 | 0 (depuis cleanup) ✅ |
| **Build Time MCP** | 70+ min | <60min | ⏱️ En cours |

---

## 🎯 DÉCISION GO/NO-GO PHASE 1

### **Après Phase 0, évaluer:**

**✅ GO vers Phase 1 SI:**
- Phase 0 complétée à 100%
- Infrastructure stable 7+ jours sans incidents
- Budget approuvé pour SSD ($150)
- ROI Phase 0 validé (temps gagné > temps investi)

**❌ NO-GO SI:**
- Infrastructure instable
- Trop de manual intervention encore nécessaire
- Budget non disponible

**📋 Meeting de validation**: 11 Février 2026 (J+7)

---

## 📅 PLANNING DÉTAILLÉ PHASE 0

| Jour | Tâche | Durée | Responsable |
|------|-------|-------|-------------|
| **J0 (4 Fév)** | Audit + Cleanup + Build MCP lancé | 8h | ✅ Done |
| **J1 (5 Fév)** | Finaliser MCP + Test déploiement | 4h | En attente build |
| **J2 (6 Fév)** | Rotation logs + Monitoring disk | 4h | À faire |
| **J3 (7 Fév)** | Backups automatiques + Tests | 6h | À faire |
| **J4-J7** | Observation stabilité + Documentation | 2h/j | À faire |
| **J7 (11 Fév)** | **Validation Phase 0 + Go/No-Go Phase 1** | 2h | Meeting |

**Total Phase 0**: **7 jours** (dont 4 observation)

---

## 💡 PROCHAINE ACTION IMMÉDIATE

### **MAINTENANT (19h31, 4 Février)**:

1. ⏱️ **Attendre build MCP** - Check dans 15 min
2. 📋 **Documenter session aujourd'hui** - Git commit
3. 🌙 **Pause** - Repos bien mérité!

### **DEMAIN (5 Février)**:

1. ☑️ **Vérifier build MCP terminé**
2. 🚀 **Déployer MCP si OK**
3. 🔧 **Configuration rotation logs**
4. 📦 **Setup backups automatiques**

---

## 📝 NOTES & LEARNINGS

### **Ce qui a bien fonctionné aujourd'hui:**
- ✅ Audit systématique révèle vrais problèmes
- ✅ Cleanup agressif libère 15GB rapidement
- ✅ Documentation complète créée
- ✅ Approche progressive validée

### **Challenges identifiés:**
- ⚠️ Build Docker extrêmement lent (35+ min et counting)
- ⚠️ Hardware single node = SPOF critique
- ⚠️ Logs explosent rapidement sans rotation
- ⚠️ Pas de CI/CD = builds manuels laborieux

### **Décisions prises:**
- ✅ Approche progressive (Option 3)
- ✅ Focus Phase 0 sur stabilité
- ✅ Validation ROI à chaque phase
- ✅ Pas de shortcuts - solutions durables

---

**Status Phase 0**: **50% Complété** 🟡  
**Prochaine étape**: Finaliser MCP + Backups  
**Go/No-Go Phase 1**: 11 Février 2026


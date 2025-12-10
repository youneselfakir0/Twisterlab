# TwisterLab Operations Documentation Index

## 📚 Complete Operations Reference

### Essential Documents

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[RUNBOOK.md](./RUNBOOK.md)** | Emergency response, daily ops | Incidents, maintenance, troubleshooting |
| **[UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md)** | Version upgrades, migrations | Before any upgrade or infrastructure change |
| **[PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md)** | Performance optimization | System slowness, capacity planning |

---

## 🚀 Quick Actions

### Emergency Response
```powershell
# Health check
.\scripts\devops-toolkit.ps1 -Action health -Environment production

# Emergency rollback
.\scripts\devops-toolkit.ps1 -Action rollback -Environment production

# View logs
kubectl logs deployment/twisterlab-api -n twisterlab --tail=100
```

### Monitoring
- **Grafana**: http://grafana.twisterlab.local/
- **Prometheus**: http://prometheus.twisterlab.local/
- **Alerts**: Check PagerDuty or `#twisterlab-incidents`

### Common Scenarios

**"System is down"** → [RUNBOOK.md - Common Incidents](./RUNBOOK.md#common-incidents--resolution)

**"Need to upgrade"** → [UPGRADE_GUIDE.md - Deployment Strategies](./UPGRADE_GUIDE.md#upgrade-strategies)

**"Performance issues"** → [PERFORMANCE_GUIDE.md - Optimization](./PERFORMANCE_GUIDE.md#api-optimization)

---

## 📞 Support

- **On-Call**: PagerDuty/Opsgenie
- **Incidents**: `#twisterlab-incidents` (Slack)
- **Questions**: `#twisterlab-ops` (Slack)

---

**Last Updated**: 2025-12-10  
**Maintained By**: DevOps Team

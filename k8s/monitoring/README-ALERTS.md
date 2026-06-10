# 🚨 TwisterLab Prometheus Alerting System

## Overview
Comprehensive alerting rules for monitoring TwisterLab platform health, performance, and availability.

## 📁 Files Created

| File | Purpose |
|------|---------|
| `k8s/monitoring/prometheus-alerts-twisterlab.yaml` | Main alerting rules ConfigMap |
| `k8s/monitoring/prometheus-rule-loader.yaml` | PrometheusRule CRD for Operator |
| `scripts/Deploy-PrometheusAlerts.ps1` | PowerShell deployment script |
| `scripts/deploy-prometheus-alerts.sh` | Bash deployment script |
| `docs/prometheus-alerting-setup.md` | Full setup documentation |

## 🚀 Quick Start

### Windows (PowerShell)
```powershell
cd C:\Users\Administrator\Documents\twisterlab
.\scripts\Deploy-PrometheusAlerts.ps1
```

### Linux/Mac (Bash)
```bash
cd ~/twisterlab
chmod +x scripts/deploy-prometheus-alerts.sh
./scripts/deploy-prometheus-alerts.sh
```

### Manual Deployment
```bash
kubectl apply -f k8s/monitoring/prometheus-alerts-twisterlab.yaml -n monitoring
kubectl rollout restart deployment/prometheus -n monitoring
```

## 📊 Alert Categories

### 🤖 Agent Alerts (7 rules)
- **CriticalAgentDropout** - < 3 agents online
- **LowAgentCount** - < 5 agents online
- **HighAgentErrorRate** - > 10% error rate
- **ElevatedAgentErrorRate** - > 5% error rate
- **HighAgentLatency** - > 5000ms p95 latency
- **ModerateAgentLatency** - > 2000ms p95 latency
- **NoAgentActivity** - Zero agent calls for 10 minutes

### 🏗️ Infrastructure Alerts (4 rules)
- **TwisterlabAPIDown** - API unreachable
- **TwisterlabRedisDown** - Redis unreachable
- **TwisterlabPostgresDown** - PostgreSQL unreachable
- **HighAPIResponseTime** - > 2s p95 response time

### 🎮 GPU Alerts (3 rules)
- **GPUUtilizationCriticallyLow** - < 5% utilization
- **GPUTemperatureHigh** - > 85°C temperature
- **GPUMemoryHigh** - > 90% memory usage

## ✅ Verification Steps

### 1. Check Rules Loaded
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```
Visit: http://localhost:9090/rules

### 2. View Active Alerts
Visit: http://localhost:9090/alerts

### 3. Test Alert Firing
```bash
# Simulate agent dropout
kubectl scale deployment/twisterlab-agents --replicas=2 -n twisterlab

# Wait 2 minutes, check alerts

# Restore
kubectl scale deployment/twisterlab-agents --replicas=5 -n twisterlab
```

## 🔔 Next Steps

1. **Configure Alertmanager** for notifications (Slack, PagerDuty, email)
2. **Create runbooks** for each alert type
3. **Tune thresholds** based on your baseline metrics
4. **Set up oncall rotation** for critical alerts

## 📚 Documentation
- Full setup guide: `docs/prometheus-alerting-setup.md`
- Alert dashboard: View the React artifact for visual reference

## 🎯 Current Status
- ✅ 14 alerting rules configured
- ✅ 7 critical severity alerts
- ✅ 7 warning severity alerts
- ✅ All major components covered (Agents, Infrastructure, GPU)

---
**Last Updated**: 2025-05-17  
**Author**: TwisterLab Platform Team

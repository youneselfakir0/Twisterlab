# TwisterLab Prometheus Alerting Setup Guide

## 📋 Overview
This guide sets up comprehensive alerting for your TwisterLab platform monitoring:
- **Agent Health**: Dropout detection, error rates, latency monitoring
- **Infrastructure**: API, Redis, PostgreSQL health checks
- **GPU Performance**: Utilization, temperature, memory monitoring

## 🚀 Deployment Steps

### Step 1: Apply Alert Rules ConfigMap
```bash
# Apply the alerting rules
kubectl apply -f k8s/monitoring/prometheus-alerts-twisterlab.yaml -n monitoring

# Verify ConfigMap creation
kubectl get configmap prometheus-twisterlab-alerts -n monitoring
```

### Step 2: Update Prometheus Configuration

**Option A: Using Prometheus Operator (Recommended)**
```bash
# The PrometheusRule CRD will be auto-discovered
kubectl apply -f k8s/monitoring/prometheus-rule-loader.yaml -n monitoring

# Verify rule creation
kubectl get prometheusrules -n monitoring
```

**Option B: Standalone Prometheus**
```bash
# Edit your Prometheus deployment to mount the ConfigMap
kubectl edit deployment prometheus -n monitoring

# Add volume mount:
# volumes:
#   - name: twisterlab-alerts
#     configMap:
#       name: prometheus-twisterlab-alerts
# 
# volumeMounts:
#   - name: twisterlab-alerts
#     mountPath: /etc/prometheus/rules/twisterlab-alerts.yml
#     subPath: twisterlab-alerts.yml

# Reload Prometheus configuration
kubectl rollout restart deployment/prometheus -n monitoring
```

### Step 3: Verify Alert Rules Loaded
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Visit http://localhost:9090/rules
# You should see the "twisterlab_agents", "twisterlab_infrastructure", 
# and "twisterlab_gpu" rule groups
```

## 🎯 Alert Thresholds Summary

### Agent Alerts
| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| CriticalAgentDropout | < 3 agents | 2 min | Critical |
| LowAgentCount | < 5 agents | 5 min | Warning |
| HighAgentErrorRate | > 10% | 3 min | Critical |
| ElevatedAgentErrorRate | > 5% | 5 min | Warning |
| HighAgentLatency | > 5000ms (p95) | 3 min | Critical |
| ModerateAgentLatency | > 2000ms (p95) | 5 min | Warning |
| NoAgentActivity | 0 calls | 10 min | Critical |

### Infrastructure Alerts
| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| TwisterlabAPIDown | Service down | 1 min | Critical |
| TwisterlabRedisDown | Service down | 1 min | Critical |
| TwisterlabPostgresDown | Service down | 1 min | Critical |
| HighAPIResponseTime | > 2s (p95) | 5 min | Warning |

### GPU Alerts
| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| GPUUtilizationCriticallyLow | < 5% | 10 min | Warning |
| GPUTemperatureHigh | > 85°C | 3 min | Critical |
| GPUMemoryHigh | > 90% | 5 min | Warning |

## 🔔 Alertmanager Integration (Optional)

To receive notifications (Slack, PagerDuty, email), configure Alertmanager:

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    
    route:
      group_by: ['alertname', 'component']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'default'
      routes:
        - match:
            severity: critical
          receiver: 'critical-alerts'
    
    receivers:
      - name: 'default'
        # Configure your default notification channel
      
      - name: 'critical-alerts'
        # Slack example:
        # slack_configs:
        #   - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        #     channel: '#twisterlab-alerts'
        #     title: '🚨 {{ .GroupLabels.alertname }}'
        #     text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## 🧪 Testing Alerts

### Simulate Agent Dropout
```bash
# Scale down agent deployment
kubectl scale deployment/twisterlab-agents --replicas=2 -n twisterlab

# Wait 2 minutes, check Prometheus alerts UI
# Should see "CriticalAgentDropout" firing

# Restore
kubectl scale deployment/twisterlab-agents --replicas=5 -n twisterlab
```

### Simulate High Error Rate
```python
# Send failing requests to agent API
import requests
for i in range(100):
    try:
        requests.post("http://api.twisterlab.local/api/v1/agents/invalid", 
                     json={"invalid": "data"})
    except:
        pass
```

## 📊 Dashboard Integration

Add alert status panels to your Grafana dashboard:

```json
{
  "type": "stat",
  "title": "Active Alerts",
  "targets": [{
    "expr": "count(ALERTS{alertstate=\"firing\"})"
  }],
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "steps": [
          { "value": 0, "color": "green" },
          { "value": 1, "color": "red" }
        ]
      }
    }
  }
}
```

## 🔍 Troubleshooting

### Rules Not Loading
```bash
# Check Prometheus logs
kubectl logs -n monitoring deployment/prometheus | grep -i "rule"

# Verify ConfigMap content
kubectl get configmap prometheus-twisterlab-alerts -n monitoring -o yaml

# Check rule syntax
promtool check rules k8s/monitoring/prometheus-alerts-twisterlab.yaml
```

### Alerts Not Firing
```bash
# Check if metrics exist
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/graph
# Run query: twisterlab_registry_agents_online

# Check alert evaluation
# Visit http://localhost:9090/alerts
```

## 📚 Next Steps

1. **Configure Alertmanager** for notifications
2. **Create runbooks** for each alert type
3. **Set up oncall rotation** for critical alerts
4. **Tune thresholds** based on your baseline metrics
5. **Add custom alerts** for business-specific metrics

---
**Note**: Adjust thresholds based on your specific SLOs and baseline performance metrics.

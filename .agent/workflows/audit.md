---
description: Infrastructure audit for TwisterLab Kubernetes cluster on EdgeServer (192.168.0.30)
---

# Infrastructure Audit Workflow

This workflow performs a comprehensive health check of the TwisterLab Kubernetes infrastructure.

## Pre-requisites
- kubectl configured to connect to the EdgeServer cluster (192.168.0.30)
- Appropriate RBAC permissions to view cluster resources

---

## 1. Cluster Node Health
// turbo
```bash
kubectl get nodes -o wide
```
Check that all nodes are in `Ready` status.

## 2. Node Resource Usage
// turbo
```bash
kubectl top nodes
```
Verify CPU and memory usage are within acceptable limits (<80% recommended).

## 3. All Pods Status (All Namespaces)
// turbo
```bash
kubectl get pods --all-namespaces -o wide
```
Look for any pods not in `Running` or `Completed` status.

## 4. Deployments Status
// turbo
```bash
kubectl get deployments --all-namespaces
```
Ensure all deployments have READY = desired count.

## 5. Services Overview
// turbo
```bash
kubectl get services --all-namespaces
```
Verify all expected services exist and have correct types (NodePort/ClusterIP/LoadBalancer).

## 6. Pod Resource Usage
// turbo
```bash
kubectl top pods --all-namespaces
```
Identify any pods with unusually high CPU or memory consumption.

## 7. Recent Events (Last 20)
// turbo
```bash
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -20
```
Look for Warning events or errors that need attention.

## 8. HorizontalPodAutoscalers
// turbo
```bash
kubectl get hpa --all-namespaces
```
Check for any HPA with `<unknown>` targets or referencing non-existent deployments.

## 9. Persistent Volumes & Claims
// turbo
```bash
kubectl get pv,pvc --all-namespaces
```
Verify all PVCs are in `Bound` status.

## 10. Ingress Configuration
// turbo
```bash
kubectl get ingress --all-namespaces
```
Confirm ingress rules are properly configured.

## 11. Monitoring Stack Health
// turbo
```bash
kubectl get all -n monitoring
```
Ensure Prometheus and Grafana pods are running.

## 12. MCP Server Health Check
// turbo
```bash
kubectl logs -n default -l app=mcp-server --tail=10
```
Verify health check endpoints are returning 200 OK.

## 13. TwisterLab Namespace Status
// turbo
```bash
kubectl get all -n twisterlab
```
Check all TwisterLab components are running correctly.

## 14. ConfigMaps Inventory
// turbo
```bash
kubectl get configmaps --all-namespaces | Select-String -Pattern "twisterlab|monitoring|mcp|prometheus|grafana"
```
Verify expected configurations exist.

---

## Common Issues & Fixes

### Orphaned HPA
If an HPA references a non-existent deployment:
```bash
kubectl delete hpa <hpa-name> -n <namespace>
```

### Pod CrashLoopBackOff
Check pod logs for error details:
```bash
kubectl logs <pod-name> -n <namespace> --previous
kubectl describe pod <pod-name> -n <namespace>
```

### PVC Pending
Check storage class and available capacity:
```bash
kubectl describe pvc <pvc-name> -n <namespace>
kubectl get storageclass
```

### Node NotReady
Check node conditions:
```bash
kubectl describe node <node-name>
```

---

## Expected Healthy State

| Component | Expected Status |
|-----------|-----------------|
| Node | Ready |
| CPU Usage | <80% |
| Memory Usage | <80% |
| All Pods | Running/Completed |
| Deployments | READY = desired |
| PVCs | Bound |
| HPAs | Valid targets, no unknown |
| MCP Server | Health checks 200 OK |
| Prometheus | Running |
| Grafana | Running |

---

## Return Condition
Report a summary table of:
1. Overall cluster health (Healthy/Degraded/Critical)
2. Number of issues found by severity (Critical/Warning/Info)
3. List of specific issues with recommended actions
4. Resource utilization summary

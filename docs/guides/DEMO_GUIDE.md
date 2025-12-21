# 🎥 TwisterLab Demo Guide

This guide helps you prepare for and execute a smooth demonstration of the TwisterLab platform.

## 🚀 1. Start Support Stack (Demo Mode)

We have created a dedicated Compose configuration optimized for demos (fast start, mocks enabled).

```bash
docker compose -f docker-compose.demo.yml up -d --build
```

Wait 30-60 seconds for services to initialize.

**Verify Health:**

1. **API (System):**
```bash
curl http://localhost:8001/api/v1/system/health
# Expected: {"status":"healthy"}
```

2. **MCP (Reflexes Tools):**
```bash
curl http://localhost:8081/health
# Expected: {"status":"healthy", "tools": ...}
```

## 🎬 2. Run the Autonomous Incident Scenario

This scenario demonstrates an end-to-end workflow: ticket intake -> classification -> investigation -> remediation.

**Run the script:**
```bash
python demos/autonomous_incident.py
```

**What to show:**
1.  **Terminal Output:** The script prints pretty emojis and step-by-step actions.
2.  **Grafana (http://localhost:3001):** Show the "Agent Execution" metrics spiking. (Login: admin/demo).
3.  **Logs:** `docker compose -f docker-compose.demo.yml logs -f api` to show real-time agent reasoning.


## 🧹 3. Cleanup

To stop and remove demo resources:

```bash
docker compose -f docker-compose.demo.yml down -v
```

## 📸 Checklist for Video

- [ ] **Clean Desktop:** Close unnecessary windows.
- [ ] **Terminal:** Use a clean font (e.g., Cascadia Code), slightly zoomed in.
- [ ] **Browser:** Have Grafana (localhost:3000) and API Health (localhost:8000/health) tabs ready.
- [ ] **Narrative:** "TwisterLab isn't just a chatbot; it's an operating system for agents."

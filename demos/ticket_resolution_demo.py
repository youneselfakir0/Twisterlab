#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TwisterLab — Démo End-to-End : Résolution Automatique de Ticket
================================================================

Scénario : "Notre application web ne répond plus depuis 10 minutes"

Ce script simule le pipeline complet de TwisterLab :
  1. Analyse du sentiment (urgence critique ?)
  2. Classification du ticket (DATABASE/APP/NETWORK...)
  3. Orchestration Maestro (plan multi-agents)
  4. Documentation automatique dans Notion

Usage :
  # Mode simulation (aucun service requis)
  python demos/ticket_resolution_demo.py

  # Mode réel (API TwisterLab running)
  TWISTERLAB_API=http://192.168.0.30:30000 python demos/ticket_resolution_demo.py --live

  # Mode MCP direct (agents Python)
  python demos/ticket_resolution_demo.py --direct
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Force UTF-8 sur Windows (évite UnicodeEncodeError avec les emojis/accents)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

API_BASE = os.getenv("TWISTERLAB_API", "http://localhost:8000")
DEMO_TICKET = "Notre application web ne répond plus depuis 10 minutes. Les clients ne peuvent pas accéder au site. C'est critique!"
NOTION_ENABLED = bool(os.getenv("NOTION_TOKEN"))

COLORS = {
    "reset":  "\033[0m",
    "bold":   "\033[1m",
    "red":    "\033[91m",
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "blue":   "\033[94m",
    "purple": "\033[95m",
    "cyan":   "\033[96m",
    "white":  "\033[97m",
    "gray":   "\033[90m",
}


def c(color: str, text: str) -> str:
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def header(title: str) -> None:
    width = 70
    print()
    print(c("purple", "─" * width))
    print(c("bold", f"  {title}"))
    print(c("purple", "─" * width))


def step(num: int, agent: str, action: str) -> None:
    print(f"\n  {c('cyan', f'[{num}]')} {c('yellow', agent)} → {c('white', action)}")


def result_ok(data: Dict[str, Any]) -> None:
    print(c("green", f"      ✅ OK — {json.dumps(data, ensure_ascii=False)[:120]}"))


def result_err(error: str) -> None:
    print(c("red", f"      ❌ ERROR — {error[:120]}"))


def result_sim(data: Dict[str, Any]) -> None:
    print(c("gray", f"      ◎ SIM — {json.dumps(data, ensure_ascii=False)[:120]}"))


# ──────────────────────────────────────────────────────────────────────────────
# Mode SIMULATION (standalone — aucune dépendance)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SimResult:
    agent: str
    action: str
    data: Dict[str, Any]
    duration_ms: int
    success: bool = True

@dataclass
class DemoReport:
    ticket: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    steps: List[SimResult] = field(default_factory=list)
    mission_id: str = ""
    total_duration_ms: int = 0
    notion_url: Optional[str] = None


async def run_simulation(ticket: str) -> DemoReport:
    """Simulation complète sans aucun service externe."""
    report = DemoReport(ticket=ticket)
    mission_id = f"M-{datetime.now().strftime('%Y%m%d')}-{abs(hash(ticket)) % 1000:03d}"
    report.mission_id = mission_id
    t0 = time.perf_counter()

    header(f"🌀 TWISTERLAB — DÉMO END-TO-END [SIMULATION]")
    print(f"\n  {c('white', 'Ticket')} : {c('yellow', ticket[:80])}")
    print(f"  {c('white', 'Mission')} : {c('cyan', mission_id)}")
    print(f"  {c('white', 'Mode')} : {c('gray', 'Simulation (aucun service requis)')}")

    # ── Step 1 : Sentiment Analysis ──────────────────────────────────────────
    step(1, "SentimentAnalyzerAgent", "analyze_sentiment")
    await asyncio.sleep(0.15)
    sentiment_data = {
        "sentiment": "NEGATIVE",
        "urgency": "CRITICAL",
        "confidence": 0.96,
        "keywords": ["ne répond plus", "10 minutes", "clients", "critique"],
    }
    result_sim(sentiment_data)
    report.steps.append(SimResult("sentiment-analyzer", "analyze_sentiment", sentiment_data, 150))

    # ── Step 2 : Classification ───────────────────────────────────────────────
    step(2, "RealClassifierAgent", "classify_ticket")
    await asyncio.sleep(0.1)
    classify_data = {
        "category": "APPLICATION",
        "subcategory": "WEB_SERVER",
        "priority": "CRITICAL",
        "confidence": 0.93,
    }
    result_sim(classify_data)
    report.steps.append(SimResult("classifier", "classify_ticket", classify_data, 100))

    # ── Step 3 : Maestro Analysis ─────────────────────────────────────────────
    step(3, "RealMaestroAgent", "analyze_task")
    await asyncio.sleep(0.2)
    analyze_data = {
        "category": "application",
        "priority": "critical",
        "suggested_agents": ["monitoring", "browser", "real-desktop-commander", "backup", "notion"],
        "source": "rules",
    }
    result_sim(analyze_data)
    report.steps.append(SimResult("maestro", "analyze_task", analyze_data, 200))

    # ── Step 4 : System Monitoring ────────────────────────────────────────────
    step(4, "RealMonitoringAgent", "get_system_metrics")
    await asyncio.sleep(0.3)
    metrics_data = {
        "cpu_percent": 12.4,
        "memory_percent": 67.2,
        "disk_percent": 44.1,
        "nginx_status": "DOWN",
        "error": "nginx: connection refused",
        "uptime": "5 days, 3:22:11",
    }
    result_sim(metrics_data)
    report.steps.append(SimResult("monitoring", "get_system_metrics", metrics_data, 300))

    # ── Step 5 : Browser Verification ────────────────────────────────────────
    step(5, "RealBrowserAgent", "browse (https://app.example.com)")
    await asyncio.sleep(0.4)
    browse_data = {
        "url": "https://app.example.com",
        "status_code": 502,
        "error": "Bad Gateway — nginx upstream failed",
        "screenshot_taken": True,
    }
    result_sim(browse_data)
    report.steps.append(SimResult("browser", "browse", browse_data, 400))

    # ── Step 6 : Backup avant intervention ───────────────────────────────────
    step(6, "RealBackupAgent", "create_backup (nginx-config)")
    await asyncio.sleep(0.2)
    backup_data = {
        "backup_id": f"BK-{datetime.now().strftime('%Y%m%d%H%M')}",
        "service": "nginx-config",
        "status": "COMPLETED",
        "size_mb": 12,
    }
    result_sim(backup_data)
    report.steps.append(SimResult("backup", "create_backup", backup_data, 200))

    # ── Step 7 : Desktop Commander ────────────────────────────────────────────
    step(7, "RealDesktopCommanderAgent", "execute_command (systemctl restart nginx)")
    await asyncio.sleep(0.5)
    cmd_data = {
        "command": "systemctl restart nginx",
        "exit_code": 0,
        "stdout": "● nginx.service — A high performance web server\n   Active: active (running)",
        "success": True,
    }
    result_sim(cmd_data)
    report.steps.append(SimResult("real-desktop-commander", "execute_command", cmd_data, 500))

    # ── Step 8 : Vérification post-fix ───────────────────────────────────────
    step(8, "RealBrowserAgent", "browse (vérification post-fix)")
    await asyncio.sleep(0.3)
    verify_data = {
        "url": "https://app.example.com",
        "status_code": 200,
        "title": "App | Dashboard",
        "success": True,
    }
    result_sim(verify_data)
    report.steps.append(SimResult("browser", "browse_verify", verify_data, 300))

    # ── Step 9 : Resolution ───────────────────────────────────────────────────
    step(9, "RealResolverAgent", "resolve_ticket")
    await asyncio.sleep(0.1)
    resolution_data = {
        "ticket_id": "TICKET-AUTO",
        "resolution": "Nginx service restarted automatically",
        "actions_taken": ["monitoring_check", "backup_config", "service_restart", "web_verification"],
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    result_sim(resolution_data)
    report.steps.append(SimResult("resolver", "resolve_ticket", resolution_data, 100))

    # ── Step 10 : Notion Documentation ───────────────────────────────────────
    step(10, "RealNotionAgent", "log_mission")
    await asyncio.sleep(0.15)
    notion_data: Dict[str, Any]
    if NOTION_ENABLED:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
            from twisterlab.agents.real.real_notion_agent import RealNotionAgent
            agent = RealNotionAgent()
            result = await agent.handle_log_mission(
                mission_id=mission_id,
                task=ticket,
                status="completed",
                findings=["Nginx service arrêté (OOM killed)", "Site retourné HTTP 502"],
                resolution="Nginx redémarré via systemctl. Config sauvegardée.",
                agents_used=["sentiment-analyzer", "classifier", "monitoring", "browser", "backup", "real-desktop-commander"],
            )
            if result.success:
                notion_data = result.data or {}
                report.notion_url = notion_data.get("url")
                result_ok(notion_data)
            else:
                notion_data = {"error": result.error, "note": "Non-bloquant"}
                result_err(result.error or "Notion unavailable")
        except Exception as e:
            notion_data = {"note": f"Notion non configuré: {e}"}
            result_sim(notion_data)
    else:
        notion_data = {
            "page_id": f"sim-{mission_id.lower()}",
            "title": f"[{mission_id}] Application web down...",
            "url": f"https://notion.so/sim-{mission_id.lower()}",
            "note": "Simulation (NOTION_TOKEN non configuré)",
        }
        result_sim(notion_data)

    report.steps.append(SimResult("notion", "log_mission", notion_data, 150))

    # ── Rapport Final ─────────────────────────────────────────────────────────
    report.total_duration_ms = int((time.perf_counter() - t0) * 1000)
    success_count = sum(1 for s in report.steps if s.success)

    header("📊 RAPPORT DE MISSION")
    print(f"""
  {c('bold', 'Mission ID')}    : {c('cyan', mission_id)}
  {c('bold', 'Ticket')}       : {ticket[:60]}
  {c('bold', 'Durée totale')} : {c('green', f'{report.total_duration_ms}ms')}
  {c('bold', 'Étapes')}       : {c('green', str(success_count))}/{len(report.steps)} réussies
  {c('bold', 'Diagnostic')}   : {c('red', 'Nginx service arrêté (OOM killed)')}
  {c('bold', 'Résolution')}   : {c('green', 'Nginx redémarré automatiquement ✅')}
  {c('bold', 'Notion')}       : {c('cyan', report.notion_url or 'Non configuré (NOTION_TOKEN manquant)')}
""")

    print(c("purple", "─" * 70))
    print(c("green", "  ✅ TICKET RÉSOLU EN < 3 SECONDES (simulation)"))
    print(c("purple", "─" * 70))
    print()
    print(f"  {c('gray', 'Pour activer Notion : ajoutez NOTION_TOKEN dans le .env')}")
    print(f"  {c('gray', 'Pour le mode live   : TWISTERLAB_API=http://192.168.0.30:30000 python demos/ticket_resolution_demo.py --live')}")
    print()

    return report


# ──────────────────────────────────────────────────────────────────────────────
# Mode LIVE (via API REST TwisterLab)
# ──────────────────────────────────────────────────────────────────────────────

async def run_live(ticket: str) -> DemoReport:
    """Mode live — appelle l'API TwisterLab réelle."""
    try:
        import httpx
    except ImportError:
        print(c("red", "❌ httpx requis : pip install httpx"))
        sys.exit(1)

    report = DemoReport(ticket=ticket)
    t0 = time.perf_counter()

    header(f"🌀 TWISTERLAB — DÉMO END-TO-END [LIVE]")
    print(f"\n  {c('white', 'API')}    : {c('cyan', API_BASE)}")
    print(f"  {c('white', 'Ticket')} : {c('yellow', ticket[:80])}")

    async with httpx.AsyncClient(base_url=API_BASE, timeout=60.0) as client:

        # Health check
        try:
            health = await client.get("/health")
            print(f"  {c('white', 'Status')} : {c('green', health.json().get('status', 'ok'))}")
        except Exception as e:
            print(c("red", f"  ❌ API non joignable : {e}"))
            print(c("yellow", "  → Basculement en mode simulation..."))
            return await run_simulation(ticket)

        # Step 1 : Sentiment
        step(1, "SentimentAnalyzerAgent", "analyze_sentiment")
        try:
            r = await client.post("/v1/mcp/tools/analyze_sentiment", json={"text": ticket, "detailed": True})
            data = r.json().get("data", {})
            result_ok(data)
            report.steps.append(SimResult("sentiment-analyzer", "analyze_sentiment", data, 0))
        except Exception as e:
            result_err(str(e))

        # Step 2 : Classify
        step(2, "RealClassifierAgent", "classify_ticket")
        try:
            r = await client.post("/v1/mcp/tools/classify_ticket", json={"description": ticket})
            data = r.json().get("data", {})
            result_ok(data)
            report.steps.append(SimResult("classifier", "classify_ticket", data, 0))
        except Exception as e:
            result_err(str(e))

        # Step 3 : Maestro Orchestrate
        step(3, "RealMaestroAgent", "orchestrate")
        try:
            r = await client.post("/v1/mcp/tools/orchestrate", json={
                "task": ticket,
                "context": {"demo": True},
                "dry_run": False,
            })
            data = r.json().get("data", {})
            result_ok(data)
            report.mission_id = data.get("mission_id", "")
            report.notion_url = data.get("notion_url")
            report.steps.append(SimResult("maestro", "orchestrate", data, 0))
        except Exception as e:
            result_err(str(e))

    report.total_duration_ms = int((time.perf_counter() - t0) * 1000)
    header("📊 RÉSULTAT")
    print(f"\n  Mission {c('cyan', report.mission_id)} terminée en {c('green', str(report.total_duration_ms) + 'ms')}\n")
    return report


# ──────────────────────────────────────────────────────────────────────────────
# Mode DIRECT (agents Python directs)
# ──────────────────────────────────────────────────────────────────────────────

async def run_direct(ticket: str) -> None:
    """Mode direct — import Python des agents."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

    header("🌀 TWISTERLAB — DÉMO END-TO-END [DIRECT AGENTS]")
    print(f"\n  {c('white', 'Ticket')} : {c('yellow', ticket[:80])}")
    print(f"  {c('white', 'Mode')}   : {c('cyan', 'Import Python direct (agents réels)')}\n")

    try:
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent

        step(1, "SentimentAnalyzerAgent", "analyze_sentiment")
        r = await SentimentAnalyzerAgent().execute("analyze_sentiment", text=ticket, detailed=True)
        if r.success:
            result_ok(r.data)
        else:
            result_err(r.error or "unknown")

        step(2, "RealClassifierAgent", "classify_ticket")
        r = await RealClassifierAgent().execute("classify_ticket", ticket_text=ticket)
        if r.success:
            result_ok(r.data)
        else:
            result_err(r.error or "unknown")

        step(3, "RealMaestroAgent", "analyze_task")
        r = await RealMaestroAgent().execute("analyze_task", task=ticket)
        if r.success:
            result_ok(r.data)
        else:
            result_err(r.error or "unknown")

    except ImportError as e:
        print(c("red", f"\n  ❌ Import failed: {e}"))
        print(c("yellow", "  → Vérifiez PYTHONPATH=src ou installez les dépendances"))
        print(c("gray",   "  → Basculement en mode simulation..."))
        await run_simulation(ticket)


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    args = sys.argv[1:]

    # Ticket personnalisé
    if "--ticket" in args:
        idx = args.index("--ticket")
        ticket = args[idx + 1] if idx + 1 < len(args) else DEMO_TICKET
    else:
        ticket = DEMO_TICKET

    if "--live" in args:
        await run_live(ticket)
    elif "--direct" in args:
        await run_direct(ticket)
    else:
        await run_simulation(ticket)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TwisterLab — Démo End-to-End : Automatisation Métier (Support + Stock + Commandes)
================================================================================

Scénario : "Le client signale une rupture de stock critique sur un produit vital."

Ce script simule la collaboration entre agents de support et agents métier :
  1. Support : Analyse du sentiment et classification de l'urgence.
  2. Métier : Vérification du stock réel via RealStockManagerAgent (n8n).
  3. Métier : Création automatique d'une commande via RealOrderProcessorAgent (n8n).
  4. Documentation : Archivage de la mission dans Notion.
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

# Force UTF-8 sur Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────────────────────
# UI Helpers
# ──────────────────────────────────────────────────────────────────────────────

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
    print(f"\n{c('purple', '═' * 80)}")
    print(c("bold", f"  {title}"))
    print(f"{c('purple', '═' * 80)}")

def step(num: int, agent: str, action: str) -> None:
    print(f"\n  {c('cyan', f'[{num}]')} {c('yellow', agent.ljust(25))} → {c('white', action)}")

def result_sim(data: Dict[str, Any]) -> None:
    print(c("gray", f"      ◎ SIM DATA — {json.dumps(data, ensure_ascii=False)[:120]}..."))

# ──────────────────────────────────────────────────────────────────────────────
# Simulation Engine
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SimResult:
    agent: str
    action: str
    data: Dict[str, Any]
    success: bool = True

async def run_business_simulation(request: str):
    t0 = time.perf_counter()
    mission_id = f"BUS-{datetime.now().strftime('%Y%m%d')}-{abs(hash(request)) % 1000:03d}"
    
    header(f"🌀 TWISTERLAB — DÉMO AUTOMATISATION MÉTIER")
    print(f"  {c('white', 'Requête')} : {c('yellow', request)}")
    print(f"  {c('white', 'Mission')} : {c('cyan', mission_id)}")
    print(f"  {c('white', 'Mode')}    : {c('gray', 'Simulation Intégrée (Support + Métiers)')}")

    # --- ÉTAPE 1 : ANALYSE DU SENTIMENT (Support) ---
    step(1, "SentimentAnalyzer", "analyze_sentiment")
    await asyncio.sleep(0.5)
    sentiment = {"sentiment": "ANXIOUS", "urgency": "HIGH", "score": 0.88}
    result_sim(sentiment)

    # --- ÉTAPE 2 : CLASSIFICATION (Support) ---
    step(2, "RealClassifier", "classify_ticket")
    await asyncio.sleep(0.5)
    classification = {"category": "LOGISTICS", "priority": "URGENT", "confidence": 0.95}
    result_sim(classification)

    # --- ÉTAPE 3 : ORCHESTRATION MAESTRO ---
    step(3, "RealMaestro", "orchestrate_business_task")
    await asyncio.sleep(0.8)
    msg = c("purple", "→ Maestro décide d'impliquer les agents métier Stock et Order.")
    print(f"      {msg}")
    
    # --- ÉTAPE 4 : VÉRIFICATION STOCK (Métier) ---
    step(4, "RealStockManager", "check_inventory (Seringue 5ml)")
    await asyncio.sleep(1.0)
    # Simulation de la réponse du webhook n8n
    stock_response = {
        "product": "Seringue 5ml",
        "current_stock": 12,
        "threshold": 100,
        "status": "CRITICAL_LOW",
        "location": "Warehouse-Alpha"
    }
    result_sim(stock_response)
    print(f"      {c('red', '      ⚠ ALERTE : Stock critique (12) inférieur au seuil (100).')}")

    # --- ÉTAPE 5 : CRÉATION COMMANDE (Métier) ---
    step(5, "RealOrderProcessor", "create_order (Restock 500 units)")
    await asyncio.sleep(1.2)
    # Simulation de la création de commande via n8n -> ERP
    order_response = {
        "order_id": "ORD-2026-9921",
        "status": "CREATED",
        "vendor": "MedSupply Global",
        "items": [{"sku": "SER-5ML", "qty": 500}],
        "estimated_delivery": "2026-06-25"
    }
    result_sim(order_response)
    print(f"      {c('green', '      ✅ Commande ORD-2026-9921 créée avec succès.')}")

    # --- ÉTAPE 6 : DOCUMENTATION (Notion) ---
    step(6, "RealNotionAgent", "log_mission (Documentation finale)")
    await asyncio.sleep(0.7)
    notion_data = {
        "page_url": f"https://notion.so/twisterlab/mission-{mission_id}",
        "status": "ARCHIVED"
    }
    result_sim(notion_data)

    # --- BILAN FINAL ---
    duration = time.perf_counter() - t0
    print(f"\n{c('purple', '═' * 80)}")
    print(c("bold", "  📊 BILAN DE L'AUTOMATISATION MÉTIER"))
    print(f"  {c('white', 'Statut')}          : {c('green', 'RÉSOLU ✅')}")
    print(f"  {c('white', 'Temps de cycle')}  : {c('green', f'{duration:.2f}s')}")
    print(f"  {c('white', 'Action Métier')}   : {c('cyan', 'Réapprovisionnement auto déclenché (500 unités)')}")
    print(f"  {c('white', 'Économie Humaine')}: {c('yellow', 'Estimation 15 minutes de traitement manuel')}")
    print(f"{c('purple', '═' * 80)}\n")

if __name__ == "__main__":
    request = "Besoin urgent de Seringue 5ml, on est presque à sec au bloc opératoire!"
    asyncio.run(run_business_simulation(request))

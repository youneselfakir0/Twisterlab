#!/usr/bin/env python
"""Validate Grafana Dashboard JSON."""

import json
import sys
from pathlib import Path


def validate_dashboard(filepath: str) -> bool:
    """Validate a Grafana dashboard JSON file."""
    print("=" * 60)
    print("🔍 VALIDATION DASHBOARD GRAFANA")
    print("=" * 60)
    
    try:
        with open(filepath, encoding="utf-8") as f:
            d = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filepath}")
        return False
    
    # Metadata
    print("\n📋 [METADATA]")
    print(f"   Titre: {d.get('title')}")
    print(f"   UID: {d.get('uid')}")
    print(f"   Refresh: {d.get('refresh')}")
    print(f"   Schema Version: {d.get('schemaVersion')}")
    print(f"   Tags: {d.get('tags')}")
    
    # Panels
    panels = d.get("panels", [])
    rows = [p for p in panels if p.get("type") == "row"]
    data_panels = [p for p in panels if p.get("type") != "row"]
    
    print("\n📊 [PANELS]")
    print(f"   Total: {len(panels)}")
    print(f"   Sections (rows): {len(rows)}")
    print(f"   Data Panels: {len(data_panels)}")
    
    # Panel types
    types = {}
    for p in data_panels:
        t = p.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    
    print("\n📈 [TYPES DE PANELS]")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        emoji = {
            "stat": "📊",
            "timeseries": "📈",
            "gauge": "🎯",
            "table": "📋",
            "piechart": "🥧",
            "heatmap": "🔥",
        }.get(t, "📦")
        print(f"   {emoji} {t}: {c}")
    
    # Sections detail
    print("\n📁 [SECTIONS]")
    for r in rows:
        title = r.get("title", "Untitled")
        print(f"   • {title}")
    
    # Datasources check
    datasources = set()
    for p in data_panels:
        ds = p.get("datasource", {})
        if isinstance(ds, dict):
            datasources.add(ds.get("uid", "unknown"))
    
    print("\n🔌 [DATASOURCES]")
    for ds in datasources:
        status = "✅" if ds == "prometheus" else "⚠️"
        print(f"   {status} {ds}")
    
    # Validate targets (queries)
    panels_with_queries = 0
    panels_without_queries = []
    
    for p in data_panels:
        targets = p.get("targets", [])
        if targets:
            panels_with_queries += 1
        else:
            panels_without_queries.append(p.get("title", "Untitled"))
    
    print("\n🎯 [QUERIES]")
    print(f"   Panels avec queries: {panels_with_queries}/{len(data_panels)}")
    if panels_without_queries:
        print(f"   ⚠️ Sans queries: {panels_without_queries[:3]}...")
    
    # Grid positions check
    print("\n📐 [LAYOUT]")
    max_y = max((p.get("gridPos", {}).get("y", 0) + p.get("gridPos", {}).get("h", 0)) for p in panels)
    print(f"   Hauteur totale: {max_y} unités")
    
    # Final validation
    print("\n" + "=" * 60)
    
    errors = []
    if not d.get("title"):
        errors.append("Titre manquant")
    if not d.get("uid"):
        errors.append("UID manquant")
    if len(data_panels) == 0:
        errors.append("Aucun panel de données")
    
    if errors:
        print(f"❌ VALIDATION ÉCHOUÉE: {errors}")
        return False
    else:
        print("✅ VALIDATION RÉUSSIE")
        print(f"   📊 {len(data_panels)} panels prêts pour Grafana")
        print("=" * 60)
        return True


if __name__ == "__main__":
    dashboard_path = sys.argv[1] if len(sys.argv) > 1 else \
        "monitoring/grafana/dashboards/twisterlab-agents-dashboard.json"
    
    success = validate_dashboard(dashboard_path)
    sys.exit(0 if success else 1)

import asyncio
import httpx
import time
import json
import random

# Local MCP Server URL
API_URL = "http://localhost:8080/tools"

async def run_traffic_generator():
    print("🚀 GÉNÉRATEUR DE TRAFIC AGENT (Intensif - 30 secondes)")
    print("-----------------------------------------------------")
    
    test_scenarios = [
        {"tool": "sentiment-analyzer_analyze_sentiment", "args": {"text": "TwisterLab is amazing!"}},
        {"tool": "sentiment-analyzer_analyze_sentiment", "args": {"text": "This is terrible service."}},
        {"tool": "real-classifier_classify_ticket", "args": {"ticket_text": "I can't log in to my account"}},
        {"tool": "real-resolver_resolve_ticket", "args": {"ticket_id": "T-101", "resolution_note": "Fixed cable"}},
        {"tool": "real-backup_create_backup", "args": {"service_name": "redis"}},
        {"tool": "monitoring_monitoring_health_check", "args": {}},
        {"tool": "maestro_maestro_orchestrate", "args": {"task": "Build me a house"}}
    ]
    
    async with httpx.AsyncClient() as client:
        # Pre-check tools
        tools_resp = await client.get(API_URL)
        available_tools = [t["name"] for t in tools_resp.json()["tools"]]

        print(f"🔥 Lancement de la boucle de trafic (20 requêtes)...")
        for i in range(20):
            scenario = random.choice(test_scenarios)
            tool = scenario["tool"]
            
            # Auto-correction des noms de tools
            if tool not in available_tools:
                match = [t for t in available_tools if tool.split("_")[-1] in t]
                if match: tool = match[0]

            print(f"[{i+1}/20] Triggering: {tool}...", end="", flush=True)
            
            try:
                start = time.time()
                await client.post(f"{API_URL}/{tool}", json=scenario["args"], timeout=5.0)
                duration = time.time() - start
                print(f" ✅ {duration*1000:.1f}ms")
            except Exception as e:
                print(f" ❌ {e}")
            
            await asyncio.sleep(0.5)

        print("\n📈 RÉCUPÉRATION DES STATISTIQUES DU ROUTEUR OPTIMISÉ...")
        stats_resp = await client.get("http://localhost:8080/stats")
        print(json.dumps(stats_resp.json(), indent=2))

        print("\n🔥 EXPOSITION DES MÉTRIQUES PROMETHEUS (Live)...")
        metrics_resp = await client.get("http://localhost:8080/metrics")
        for line in metrics_resp.text.split("\n"):
            if "mcp_tool" in line or "agent_execution" in line:
                print(line)

if __name__ == "__main__":
    asyncio.run(run_traffic_generator())

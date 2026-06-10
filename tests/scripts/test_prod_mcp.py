import asyncio
import httpx
import time
import json
import random

# Remote Production URL
API_URL = "http://192.168.0.30:30001/tools"

async def run_traffic_generator():
    print("🚀 GÉNÉRATEUR DE TRAFIC PRODUCTION (30 secondes)")
    print(f"Target: {API_URL}")
    print("-----------------------------------------------------")
    
    test_scenarios = [
        {"tool": "sentiment-analyzer_analyze_sentiment", "args": {"text": "TwisterLab is amazing!"}},
        {"tool": "real-classifier_classify_ticket", "args": {"ticket_text": "I can't log in to my account"}},
        {"tool": "real-resolver_resolve_ticket", "args": {"ticket_id": "T-101", "resolution_note": "Fixed cable"}},
        {"tool": "real-backup_create_backup", "args": {"service_name": "redis"}},
        {"tool": "monitoring_monitoring_health_check", "args": {}},
        {"tool": "maestro_maestro_orchestrate", "args": {"task": "Check system health"}}
    ]
    
    async with httpx.AsyncClient() as client:
        # Pre-check tools
        print("🔍 Checking available tools...")
        try:
            tools_resp = await client.get(API_URL, timeout=5.0)
            if tools_resp.status_code != 200:
                print(f"❌ API Error: {tools_resp.status_code}")
                return
            available_tools = [t["name"] for t in tools_resp.json()["tools"]]
            print(f"✅ Found {len(available_tools)} tools.")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            return

        print(f"🔥 Lancement de la boucle de trafic (30 requêtes)...")
        for i in range(30):
            scenario = random.choice(test_scenarios)
            tool = scenario["tool"]
            
            # Auto-correction
            if tool not in available_tools:
                match = [t for t in available_tools if tool.split("_")[-1] in t]
                if match: tool = match[0]

            print(f"[{i+1}/30] Triggering: {tool}...", end="", flush=True)
            
            try:
                start = time.time()
                headers = {"Authorization": "Bearer dev-token-admin"}
                resp = await client.post(f"{API_URL}/{tool}", json=scenario["args"], headers=headers, timeout=10.0)
                duration = time.time() - start
                
                if resp.status_code == 200:
                    print(f" ✅ {duration*1000:.1f}ms")
                else:
                    print(f" ❌ {resp.status_code}")
            except Exception as e:
                print(f" ❌ {e}")
            
            await asyncio.sleep(0.2)

        print("\n📈 RÉCUPÉRATION DES STATISTIQUES ROUTEUR...")
        try:
            stats_resp = await client.get("http://192.168.0.30:30001/stats")
            print(json.dumps(stats_resp.json(), indent=2))
        except:
            print("Stats endpoint not reachable via 30001 directly (mapped to tools only?) or error.")

if __name__ == "__main__":
    asyncio.run(run_traffic_generator())

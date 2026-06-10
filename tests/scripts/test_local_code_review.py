import asyncio
import httpx
import time
import json
import random

# Local MCP Server URL
API_URL = "http://localhost:8080/tools"
# Magic token for Admin rights (to bypass RBAC locally without full AzureAD)
AUTH_HEADERS = {"Authorization": "Bearer dev-token-admin"}

async def run_traffic_generator():
    print("🚀 TEST UNITAIRE: CODE REVIEW AGENT (Plus autres)")
    print("-----------------------------------------------------")
    
    test_scenarios = [
        {"tool": "code-review_analyze_code", "args": {"code": "print('Hello world'); v = eval('2+2')", "language": "python"}},
        {"tool": "code-review_security_scan", "args": {"code": "password = 'secret_123'; print(password)"}},
        {"tool": "sentiment-analyzer_analyze_sentiment", "args": {"text": "TwisterLab is amazing!"}},
    ]
    
    async with httpx.AsyncClient() as client:
        # Pre-check tools
        print(f"Connecting to {API_URL} (waiting for startup)...")
        for _ in range(5):
             try:
                tools_resp = await client.get(API_URL, headers=AUTH_HEADERS)
                if tools_resp.status_code == 200:
                    break
             except Exception:
                 await asyncio.sleep(1)
        else:
             print("❌ Failed to connect to local server.")
             return

        available_tools = [t["name"] for t in tools_resp.json()["tools"]]
        print(f"Server UP. Tools available: {len(available_tools)}")
        if "code-review_analyze_code" in available_tools:
            print("✅ CodeReview agent detected!")
        else:
            print("❌ CodeReview agent NOT found in tool list!")
            print(f"List: {available_tools}")

        print(f"\n🔥 Running Tests...")
        for i, scenario in enumerate(test_scenarios):
            tool = scenario["tool"]
            
            # Auto-correction
            if tool not in available_tools:
                match = [t for t in available_tools if tool.split("_")[-1] in t]
                if match: tool = match[0]

            print(f"[{i+1}/{len(test_scenarios)}] Triggering: {tool}...", end="", flush=True)
            
            try:
                start = time.time()
                resp = await client.post(f"{API_URL}/{tool}", json=scenario["args"], headers=AUTH_HEADERS, timeout=10.0)
                duration = time.time() - start
                
                if resp.status_code == 200:
                    data = resp.json()["content"][0]["text"]
                    print(f" ✅ {duration*1000:.1f}ms")
                    print(f"    Result: {data[:150]}...") # Truncate
                else:
                    print(f" ❌ Status {resp.status_code}: {resp.text}")

            except Exception as e:
                print(f" ❌ {e}")
            
            await asyncio.sleep(0.5)

        print("\n📈 Stats Check...")
        stats_resp = await client.get("http://localhost:8080/stats", headers=AUTH_HEADERS)
        print(json.dumps(stats_resp.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(run_traffic_generator())

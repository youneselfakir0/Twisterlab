import asyncio
import httpx
import json

# Local MCP Server
API_URL = "http://localhost:8000"

async def test_rbac():
    print("🔒 TEST SÉCURITÉ RBAC (Local)")
    print("-----------------------------------------------------")
    
    scenarios = [
        {
            "name": "Anonymous User (No Token)",
            "token": None,
            "expect_status": 403,  # Or 401 depending on how FastAPI handles missing bearer
            "tool": "monitoring_health_check" 
        },
        {
            "name": "Admin User (Magic Token)",
            "token": "dev-token-admin",
            "expect_status": 200,
            "tool": "real-backup_create_backup", # Admin Only
            "args": {"service_name": "test"}
        },
        {
            "name": "Normal User -> Restricted Tool",
            "token": "dev-token-user",
            "expect_status": 403, # Should Fail
            "tool": "real-backup_create_backup", 
            "args": {"service_name": "test"}
        },
        {
            "name": "Normal User -> Open Tool",
            "token": "dev-token-user",
            "expect_status": 200, # Should Pass
            "tool": "sentiment-analyzer_analyze_sentiment", 
            "args": {"text": "hello"}
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for scen in scenarios:
            print(f"Testing: {scen['name']}...", end="", flush=True)
            
            headers = {}
            if scen["token"]:
                headers["Authorization"] = f"Bearer {scen['token']}"
            
            try:
                # Assuming /tools/{name}
                resp = await client.post(
                    f"{API_URL}/tools/{scen['tool']}",
                    json=scen.get("args", {}),
                    headers=headers
                )
                
                status_ok = False
                if scen["expect_status"] == 403:
                    if resp.status_code in [401, 403]: status_ok = True
                else:
                    if resp.status_code == scen["expect_status"]: status_ok = True
                
                if status_ok:
                    print(f" ✅ PASS (Got {resp.status_code})")
                else:
                    print(f" ❌ FAIL (Expected {scen['expect_status']}, Got {resp.status_code})")
                    print(f"    Response: {resp.text}")

            except Exception as e:
                print(f" ❌ EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_rbac())

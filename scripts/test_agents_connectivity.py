import httpx
import time
import json
import os

BASE_URL = "http://192.168.0.30:30080"
# Headers for admin access if needed (assuming simple bearer or api key convention from tests)
HEADERS = {
    "Authorization": "Bearer admin-key",
    "Content-Type": "application/json"
}

def test_endpoint(method, path, data=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...")
    try:
        if method == "GET":
            r = httpx.get(url, headers=HEADERS, timeout=10)
        else:
            r = httpx.post(url, json=data or {}, headers=HEADERS, timeout=10)
        
        print(f"Status: {r.status_code}")
        try:
            print(f"Response: {json.dumps(r.json(), indent=2)}")
        except:
            print(f"Response (text): {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

print("--- DIAGNOSTIC START ---")
# 1. Health check (root or /health usually)
test_endpoint("GET", "/health")
test_endpoint("GET", "/api/v1/system/health")

# 2. List agents
test_endpoint("GET", "/api/v1/mcp/tools/list_autonomous_agents")
test_endpoint("POST", "/api/v1/mcp/tools/list_autonomous_agents")

# 3. Test MCP standard list (if enabled)
test_endpoint("GET", "/tools/list")

print("--- DIAGNOSTIC END ---")

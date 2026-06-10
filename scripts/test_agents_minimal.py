import httpx
import json

BASE_URL = "http://192.168.0.30:30080"
HEADERS = {"Authorization": "Bearer dev-token-admin", "Content-Type": "application/json"}

def test(name, method, endpoint, data=None):
    print(f"--- TEST: {name} ---")
    try:
        if method == "GET":
            r = httpx.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=60)
        else:
            r = httpx.post(f"{BASE_URL}{endpoint}", json=data or {}, headers=HEADERS, timeout=60)
        
        print(f"STATUS: {r.status_code}")
        if r.status_code == 200:
            res = r.json()
            # Extract content from MCP ToolResult format
            content = res.get("content", [])
            if content and isinstance(content, list):
                print(f"RESULT: {content[0].get('text', '')[:200]}...")
            else:
                print(f"RESULT: {json.dumps(res)[:200]}...")
        else:
            print(f"ERROR: {r.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

# Test 1: Identify
test("Identify Server", "GET", "/")

# Test 2: Classifier
test("Classifier Agent", "POST", "/tools/real-classifier_classify_ticket", {
    "arguments": {
        "description": "VPN connection failed with error 691",
        "priority": "high"
    }
})

# Test 3: Resolver (Hot-fix Verification)
test("Resolver Agent (with extra params)", "POST", "/tools/real-resolver_resolve_ticket", {
    "arguments": {
        "ticket_id": "TEST-HOTFIX-001",
        "resolution_note": "Verifying kwargs fix",
        "device_id": "extra-param-should-be-ignored",
        "context": {"source": "maestro"}
    }
})

# Test 4: Monitoring
test("Monitoring Agent", "POST", "/tools/real-monitoring_monitor_system_health", {
    "arguments": {"detailed": False}
})

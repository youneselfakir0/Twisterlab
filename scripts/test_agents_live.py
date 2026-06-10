import httpx
import time
import json
import os

BASE_URL = "http://192.168.0.30:30080"
# Use magic token for admin access
HEADERS = {
    "Authorization": "Bearer dev-token-admin",
    "Content-Type": "application/json"
}

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def test_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\nRequest: {method} {url}")
    if data:
        print(f"Payload: {json.dumps(data, indent=2)}")
        
    try:
        if method == "GET":
            r = httpx.get(url, headers=HEADERS, timeout=30)
        else:
            r = httpx.post(url, json=data or {}, headers=HEADERS, timeout=30)
            
        print(f"Status: {r.status_code}")
        
        try:
            resp_json = r.json()
            # Truncate long outputs for readability
            print(f"Response: {json.dumps(resp_json, indent=2)[:500]}...")
            return resp_json
        except:
            print(f"Response (text): {r.text[:200]}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- TESTS ---

print_section("1. SERVER INFO")
test_request("GET", "/health")
test_request("GET", "/")
test_request("GET", "/agents")

print_section("2. LIST TOOLS")
tools_resp = test_request("GET", "/tools")
if tools_resp:
    tool_count = len(tools_resp.get("tools", []))
    print(f"\nFound {tool_count} tools available.")

print_section("3. TEST CLASSIFIER AGENT")
# Test resolving a ticket (classifier is cleaner to test as it has no side effects on FS like backup)
classify_payload = {
    "arguments": {
        "description": "My internet is very slow and I cannot connect to the VPN.",
        "priority": "high"
    }
}
# Tool name convention in http_server.py seems to pass through to router.execute_tool
# Usually "agent-name_tool-name". Let's try to match from the tools list if possible, or guess.
# From registry.py, classifier agent has tool "classify_ticket".
# Prefix might be "real-classifier_" or simply "classify_ticket" depending on registration.
# Let's assume standard "agent-name_tool-name" pattern: "real-classifier_classify_ticket"

test_request("POST", "/tools/real-classifier_classify_ticket", classify_payload)

print_section("4. TEST MONITORING AGENT")
monitor_payload = {
    "arguments": {
        "detailed": True
    }
}
test_request("POST", "/tools/real-monitoring_monitor_system_health", monitor_payload)

print_section("5. TEST RESOLVER AGENT (with Hot-Fix)")
resolver_payload = {
    "arguments": {
        "ticket_id": "TEST-101",
        "resolution_note": "Manual test execution",
        # Adding extra param to verify hot-fix works (should not crash)
        "device_id": "ignored-param-test" 
    }
}
test_request("POST", "/tools/real-resolver_resolve_ticket", resolver_payload)

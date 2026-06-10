
import requests
import json
import sys

# Configuration
NODE_IP = "192.168.0.30"
NODE_PORT = "30080"
BASE_URL = f"http://{NODE_IP}:{NODE_PORT}"
AUTH_HEADER = {"Authorization": "Bearer dev-token-admin"}

def log(msg, success=None):
    if success is True:
        symbol = "✅"
    elif success is False:
        symbol = "❌"
    else:
        symbol = "ℹ️"
    print(f"{symbol} {msg}")

def test_connectivity():
    log(f"Testing basic connectivity to {BASE_URL}...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            log(f"Server is UP. Version: {data.get('version')}, Tools: {data.get('tools')}", True)
            return True
        else:
            log(f"Server returned status {resp.status_code}: {resp.text}", False)
            return False
    except Exception as e:
        log(f"Connection failed: {e}", False)
        return False

def test_auth_and_tools():
    log("Testing Authentication & Tool Enumeration...")
    try:
        # 1. Try WITHOUT Auth (Should fail or show limited info, dependent on config, but normally we check secured)
        # Actually /tools might be open, but let's check WITH auth for full list
        resp = requests.get(f"{BASE_URL}/tools", headers=AUTH_HEADER, timeout=5)
        if resp.status_code == 200:
            tools = resp.json().get("tools", [])
            tool_names = [t['name'] for t in tools]
            log(f"Authenticated successfully. Found {len(tools)} tools.", True)
            if "monitoring_health_check" in tool_names:
                log("Tool 'monitoring_health_check' is PRESENT.", True)
                return True
            else:
                log("Tool 'monitoring_health_check' is MISSING.", False)
                return False
        else:
            log(f"Auth/Tools request failed: {resp.status_code} - {resp.text}", False)
            return False
    except Exception as e:
        log(f"Tool check failed: {e}", False)
        return False

def test_tool_execution():
    log("Testing Real Tool Execution (monitoring_health_check)...")
    payload = {
        "name": "monitoring_health_check",
        "arguments": {}
    }
    try:
        # Note: server.py /tools/{name} or /tools/call?
        # Let's check how the HTTP wrapper implements it.
        # Based on previous `http_server.py` view: @app.post("/tools/{tool_name}")
        url = f"{BASE_URL}/tools/monitoring_health_check"
        
        resp = requests.post(url, headers=AUTH_HEADER, json=payload, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            # print(json.dumps(result, indent=2))
            
            # Check for content results
            content = result.get("content", [])
            is_error = result.get("isError", False)
            
            if not is_error and content:
                text = content[0].get("text", "")
                log(f"Tool Execution SUCCESS. Output snippet: {text[:100]}...", True)
                return True
            else:
                log(f"Tool Execution returned ERROR: {result}", False)
                return False
        else:
            log(f"Tool Execution HTTP Failed: {resp.status_code} - {resp.text}", False)
            return False
    except Exception as e:
        log(f"Tool execution Exception: {e}", False)
        return False

def main():
    print("--- 🔍 PROOF OF LIFE: TwisterLab Production ---")
    
    step1 = test_connectivity()
    if not step1: sys.exit(1)
        
    step2 = test_auth_and_tools()
    if not step2: sys.exit(1)
        
    step3 = test_tool_execution()
    if not step3: sys.exit(1)
    
    print("\n🎉 CONCLUSION: The Production Environment is fully operational.")

if __name__ == "__main__":
    main()

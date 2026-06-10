
import requests
import sys

URL = "http://192.168.0.30:31080"
HEADERS = {"Authorization": "Bearer dev-token-admin"}

def check_health():
    try:
        print(f"Checking {URL}/health...")
        resp = requests.get(f"{URL}/health", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
        if resp.status_code == 200:
            print("Health check PASSED")
            return True
        else:
            print("Health check FAILED")
            return False
    except Exception as e:
        print(f"Health check ERROR: {e}")
        return False

def check_tools():
    try:
        print(f"Checking {URL}/tools/list...")
        # MCP uses JSON-RPC usually, but Unified MCPServer might expose HTTP endpoints for listing? 
        # The verify_prod.py used a POST to /tools/list ? Or /json-rpc?
        # Let's check verify_prod.py content to see how it talked to it.
        # But wait, verify_prod.py was viewed in summary. Let's assume standard MCP HTTP or internal endpoint.
        # Actually standard MCP running over SSE usually.
        # The previous summary mentions `verify_prod.py`. I should check it to copy the logic.
        pass
    except Exception as e:
        print(e)

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)

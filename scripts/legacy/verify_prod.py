
import requests
import sys
import time

URL = "http://192.168.0.30:30080"
HEADERS = {"Authorization": "Bearer dev-token-admin"}

def check_health():
    try:
        print(f"Checking {URL}/health...")
        resp = requests.get(f"{URL}/health", timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ Health Check PASSED: {resp.json()}")
            return True
        else:
            print(f"❌ Health Check FAILED: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Health Check ERROR: {e}")
        return False

def check_tools():
    try:
        print(f"Checking {URL}/tools with auth...")
        resp = requests.get(f"{URL}/tools", headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            tools = resp.json().get("tools", [])
            print(f"✅ Found {len(tools)} tools.")
            # Check for k8s related tools if any (e.g. MonitoringAgent)
            monitoring_tools = [t['name'] for t in tools if 'monitoring' in t['name'] or 'cluster' in t['name']]
            print(f"   Monitoring tools: {monitoring_tools}")
            return True
        else:
            print(f"❌ Tools Check FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Tools Check ERROR: {e}")
        return False

if __name__ == "__main__":
    if check_health() and check_tools():
        print("🚀 Production Environment Verification Complete")
        sys.exit(0)
    else:
        sys.exit(1)

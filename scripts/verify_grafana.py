
import requests
import sys

# Grafana Configuration
NODE_IP = "192.168.0.30"
NODE_PORT = "30300"
GRAFANA_URL = f"http://{NODE_IP}:{NODE_PORT}"

def check_grafana():
    print(f"🔍 Testing Grafana Availability at {GRAFANA_URL}...")
    try:
        # Grafana login page usually returns 200
        resp = requests.get(f"{GRAFANA_URL}/login", timeout=5)
        
        print(f"ℹ️ HTTP Status Code: {resp.status_code}")
        
        if resp.status_code == 200 and "Grafana" in resp.text:
            print("✅ Grafana is UP and responding.")
            print(f"   Dashboard Link: {GRAFANA_URL}")
            return True
        else:
            print(f"❌ Grafana responded implicitly but check failed. Preview: {resp.text[:100]}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Failed. Service might be down or firewall blocking port.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if check_grafana():
        sys.exit(0)
    else:
        sys.exit(1)

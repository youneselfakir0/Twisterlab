import requests
import json
import time

# Constants
BASE_URL = "http://192.168.0.30:30001"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev-token-admin"
}

def log(msg: str):
    print(f"[TEST] {msg}")

def test_code_review():
    log(f"Testing CodeReviewAgent on Production: {BASE_URL}")
    
    # 1. Analyze Code
    payload_analyze = {
        "arguments": {
            "code": "print('Debug'); # TODO: Fix this",
            "language": "python"
        }
    }
    
    start = time.time()
    resp = requests.post(f"{BASE_URL}/tools/code-review_analyze_code", json=payload_analyze, headers=HEADERS)
    duration = time.time() - start
    
    if resp.status_code == 200:
        data = resp.json()
        log(f"✅ Analyze Success ({duration*1000:.1f}ms): {json.dumps(data, indent=2)}")
    else:
        log(f"❌ Analyze Failed: {resp.status_code} {resp.text}")

    # 2. Security Scan
    payload_scan = {
        "arguments": {
            "code": "api_key = '123456'; eval(input())"
        }
    }
    
    start = time.time()
    resp = requests.post(f"{BASE_URL}/tools/code-review_security_scan", json=payload_scan, headers=HEADERS)
    duration = time.time() - start
    
    if resp.status_code == 200:
        data = resp.json()
        log(f"✅ Scan Success ({duration*1000:.1f}ms): {json.dumps(data, indent=2)}")
    else:
        log(f"❌ Scan Failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    test_code_review()

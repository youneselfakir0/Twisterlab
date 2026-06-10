import requests
import sys
import time
from typing import Dict, Any, Optional

# Constants
BASE_URL = "http://192.168.0.30:30001"
HEADERS = {"Content-Type": "application/json"}

# Test Data
ADMIN_TOKEN = "dev-token-admin"
USER_TOKEN = "dev-token-user"

def log(msg: str, status: str = "INFO"):
    print(f"[{status}] {msg}")

def test_tool_access(tool_name: str, token: Optional[str], expected_result_type: str, description: str):
    """
    expected_result_type: 
      "DENY" (expect 401 or 403)
      "ALLOW" (expect 200, but accept 400/500 as proof of access)
    """
    url = f"{BASE_URL}/tools/{tool_name}"
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    log(f"Testing {description}...", "TEST")
    log(f"Request: POST {url}")
    
    payload = {"arguments": {}}
    if "real-backup" in tool_name:
         payload = {"arguments": {"source_path": "/tmp", "backup_type": "full"}}
    elif "sentiment-analyzer" in tool_name:
         payload = {"arguments": {"text": "hello"}}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        status_code = response.status_code
        status_code = response.status_code
        log(f"Response: {status_code} {response.reason}")
        if status_code != 401 and status_code != 200:
             log(f"Body: {response.text[:200]}")
        if status_code == 200 and expected_result_type == "DENY":
             log(f"Startling Success Body: {response.text[:200]}")
        
        if expected_result_type == "DENY":
            if status_code in [401, 403]:
                log(f"PASS: Access Denied as expected (Got {status_code})", "PASS")
                return True
            else:
                log(f"FAIL: Access Granted! Expected 401/403, got {status_code}", "FAIL")
                return False
        
        elif expected_result_type == "ALLOW":
            if status_code == 200:
                log(f"PASS: Access Granted and Tool Executed (200)", "PASS")
                return True
            elif status_code in [400, 422, 500]:
                log(f"PASS (Partial): Access Granted (Auth Passed), but tool failed with {status_code}", "PASS")
                return True
            elif status_code in [401, 403]:
                log(f"FAIL: Access Denied! Expected Allow, got {status_code}", "FAIL")
                return False
            else:
                log(f"FAIL: Unexpected status {status_code}", "FAIL")
                return False
            
    except Exception as e:
        log(f"EXCEPTION: {str(e)}", "ERROR")
        return False

def main():
    log("Starting RBAC Verification on Production (K8s)...")
    
    # 1. Anonymous -> Restricted
    test_tool_access("real-backup_perform_backup", None, "DENY", "Anonymous Access to Restricted Tool")
    
    # 2. Admin -> Restricted
    test_tool_access("real-backup_perform_backup", ADMIN_TOKEN, "ALLOW", "Admin Access to Restricted Tool")

    # 3. User -> Restricted
    test_tool_access("real-backup_perform_backup", USER_TOKEN, "DENY", "User (Viewer) Access to Restricted Tool")

    # 4. User -> Open
    test_tool_access("sentiment-analyzer_analyze_sentiment", USER_TOKEN, "ALLOW", "User Access to Unrestricted Tool")

    log("RBAC Verification Complete.")

if __name__ == "__main__":
    main()

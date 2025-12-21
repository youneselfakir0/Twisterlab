import requests
import time
import json
import sys

# Configuration
import os
BASE_URL = os.getenv("TC_URL", "http://localhost:8081")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev-token-admin"
}

def print_step(emoji, agent, action, status="..."):
    print(f"{emoji} [{agent}] {action:<50} {status}")

def print_result(data, indent=4):
    print(json.dumps(data, indent=indent))

def wait(seconds=1):
    time.sleep(seconds)

def run_demo():
    print("\n" + "="*70)
    print(" 🎬  TWISTERLAB ENTERPRISE DEMO: AUTONOMOUS INCIDENT RESOLUTION")
    print("="*70 + "\n")
    
    # Scene 1: Intake & Classification
    ticket_text = "URGENT: I found a hardcoded password in the login module! The app is vulnerable."
    print(f"👤 [USER] Submits Ticket: \"{ticket_text}\"\n")
    wait(1)

    print_step("🧠", "Maestro", "Analyzing incoming request...")
    wait(1)
    
    print_step("🏷️", "Classifier", "Classifying ticket content...")
    resp = requests.post(f"{BASE_URL}/tools/real-classifier_classify_ticket", json={'arguments': {'ticket_text': ticket_text}}, headers=HEADERS)
    if resp.status_code == 200:
        cat = resp.json()['content'][0]['text']
        print(f"   ↳ Result: {cat}")
    else:
        print(f"   ↳ FAILED: {resp.text}")
        return

    # Scene 2: The Investigation (Code Review)
    buggy_code = "def login(u, p): secret_key = 'super_secret_123'; return True"
    print("\n" + "-"*30)
    print(f"🔍 [SYSTEM] Extracted Code Snippet:\n   {buggy_code}")
    print("-"*30 + "\n")
    
    wait(1)
    print_step("🛡️", "CodeReview", "Scanning code for vulnerabilities...")
    resp = requests.post(f"{BASE_URL}/tools/code-review_security_scan", json={'arguments': {'code': buggy_code}}, headers=HEADERS)
    if resp.status_code == 200:
        res = json.loads(resp.json()['content'][0]['text'])
        print(f"   ↳ 🚨 ALERT: {res['findings'][0]['message']}")
    
    # Scene 3: Protection (Backup)
    wait(1)
    print("\n" + "-"*30)
    print_step("💾", "Backup", "Initiating emergency backup of 'auth_db'...")
    resp = requests.post(f"{BASE_URL}/tools/real-backup_create_backup", json={'arguments': {'service_name': 'auth_db'}}, headers=HEADERS)
    if resp.status_code == 200:
        res = json.loads(resp.json()['content'][0]['text'])
        print(f"   ↳ ✅ Backup Secure: ID {res['backup_id']} ({res['size_mb']}MB)")

    # Scene 4: Resolution
    wait(1)
    print("\n" + "-"*30)
    print_step("🔧", "Resolver", "Generating SOP for remediation...")
    resp = requests.post(f"{BASE_URL}/tools/real-resolver_resolve_ticket", json={'arguments': {'ticket_id': 'INC-999', 'resolution_note': 'Removed hardcoded secret. Rotated keys.'}}, headers=HEADERS)
    if resp.status_code == 200:
        print(f"   ↳ 📄 SOP Generated: Incident INC-999 Resolved.")

    # Scene 5: Verification (Sentiment)
    wait(1)
    feedback = "Wow, TwisterLab fixed that security hole instantly. Great job!"
    print("\n" + "-"*30)
    print(f"👤 [USER] Feedback: \"{feedback}\"\n")
    
    print_step("😊", "Sentiment", "Analyzing customer satisfaction...")
    resp = requests.post(f"{BASE_URL}/tools/sentiment-analyzer_analyze_sentiment", json={'arguments': {'text': feedback}}, headers=HEADERS)
    if resp.status_code == 200:
        content = resp.json()['content'][0]['text']
        print(f"   ↳ Analysis: {content}")

    print("\n" + "="*70)
    print(" ✅ DEMO COMPLETE: INCIDENT MANAGED AUTONOMOUSLY")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")

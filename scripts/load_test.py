import requests
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor

# Target API URL (K8s Service NodePort or Ingress)
API_URL = "http://192.168.0.30:30000"
ENDPOINT = "/api/v1/system/health"

# Rate Limit Config (Match deployment)
RATE_LIMIT = 60
DURATION_SECONDS = 30
CONCURRENCY = 5

def abuse_api(worker_id):
    """Worker function to spam the API"""
    local_success = 0
    local_429 = 0
    local_errors = 0
    
    start_time = time.time()
    while time.time() - start_time < DURATION_SECONDS:
        try:
            # Add worker ID to header just in case logs track user agent
            headers = {"User-Agent": f"LoadTest/1.0 Worker-{worker_id}"}
            response = requests.get(f"{API_URL}{ENDPOINT}", headers=headers, timeout=2)
            
            if response.status_code == 200:
                local_success += 1
                sys.stdout.write(".")
            elif response.status_code == 429:
                local_429 += 1
                sys.stdout.write("x")
            else:
                local_errors += 1
                sys.stdout.write("E")
            
            sys.stdout.flush()
            
            # Sleep slightly to not kill the network adapter immediately
            time.sleep(0.1)
            
        except Exception as e:
            local_errors += 1
            if local_errors == 1:
                print(f"\n[Error Detail]: {str(e)}")
            sys.stdout.write("!")
            
    return local_success, local_429, local_errors

def run_load_test():
    print(f"🚀 Starting Load Test on {API_URL}{ENDPOINT}")
    print(f"Targeting Rate Limit: {RATE_LIMIT} req/min")
    print(f"Duration: {DURATION_SECONDS}s | Concurrency: {CONCURRENCY}")
    
    total_success = 0
    total_429 = 0
    total_errors = 0
    
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(abuse_api, i) for i in range(CONCURRENCY)]
        
        for future in futures:
            s, r, e = future.result()
            total_success += s
            total_429 += r
            total_errors += e
            
    print("\n\n📊 Load Test Results:")
    print(f"✅ Success (200): {total_success}")
    print(f"🛑 Rate Limited (429): {total_429}")
    print(f"❌ Errors: {total_errors}")
    
    total_requests = total_success + total_429 + total_errors
    print(f"Total Requests: {total_requests}")
    
    if total_429 > 0:
        print("\n✅ SECURITY VALIDATED: Rate Limiting is active and blocking excess requests.")
    elif total_requests > RATE_LIMIT:
         print("\n⚠️ WARNING: Rate Limit NOT triggered despite exceeding threshold. Check Middleware.")
    else:
         print("\nℹ️ INFO: Not enough traffic generated to trigger limit.")

if __name__ == "__main__":
    run_load_test()

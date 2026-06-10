
import requests
import time
import threading
import sys

URL = "http://192.168.0.30:30080"
HEADERS = {"Authorization": "Bearer dev-token-admin"}
THREADS = 20
DURATION = 300  # seconds

stop_event = threading.Event()

def worker(id):
    count = 0
    errors = 0
    while not stop_event.is_set():
        try:
            # Hit /tools to generate some CPU load (json parsing, etc)
            resp = requests.get(f"{URL}/tools", headers=HEADERS, timeout=2)
            if resp.status_code != 200:
                errors += 1
            # Also hit health
            requests.get(f"{URL}/health", timeout=1)
            count += 1
        except Exception:
            errors += 1
            time.sleep(0.1)
    # print(f"Worker {id} finished. Req: {count}, Err: {errors}")

def main():
    print(f"Starting Load Test on {URL} with {THREADS} threads for {DURATION}s...")
    threads = []
    for i in range(THREADS):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    start = time.time()
    try:
        while time.time() - start < DURATION:
            time.sleep(1)
            sys.stdout.write(f"\rTime remaining: {int(DURATION - (time.time() - start))}s   ")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nStopping...")
    
    stop_event.set()
    for t in threads:
        t.join()
    
    print("\nLoad Test Complete.")

if __name__ == "__main__":
    main()

import asyncio
import httpx
import time
import argparse
import sys

async def fetch(client, url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start = time.perf_counter()
    try:
        response = await client.get(url, headers=headers)
        end = time.perf_counter()
        return response.status_code, end - start
    except Exception as e:
        end = time.perf_counter()
        return str(e), end - start

async def load_test(target_url, num_requests, concurrency, token=None):
    print(f"Starting Load Test against {target_url}")
    print(f"Total Requests: {num_requests} | Concurrency: {concurrency}")
    
    limits = httpx.Limits(max_connections=concurrency)
    timeout = httpx.Timeout(10.0)
    
    results = []
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        start_time = time.time()
        
        # Batching requests to respect concurrency limits smoothly
        batches = [min(concurrency, num_requests - i) for i in range(0, num_requests, concurrency)]
        
        for batch_size in batches:
            tasks = [fetch(client, target_url, token) for _ in range(batch_size)]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
        total_time = time.time() - start_time
    
    status_codes = {}
    latencies = []
    
    for status, latency in results: # Correctly unpack status and latency
        status_codes[status] = status_codes.get(status, 0) + 1
        if isinstance(status, int) and str(status).startswith('2'):
            latencies.append(latency)
            
    success_rate = (status_codes.get(200, 0) / num_requests) * 100
    avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0
    requests_per_sec = num_requests / total_time
    
    print("\n" + "="*40)
    print("LOAD TEST RESULTS")
    print("="*40)
    print(f"Target:           {target_url}")
    print(f"Total Time:       {total_time:.2f}s")
    print(f"Requests/sec:     {requests_per_sec:.2f} rps")
    print(f"Success Rate:     {success_rate:.1f}%")
    if latencies:
        print(f"Avg Latency:      {avg_latency:.2f}ms")
        print(f"Min Latency:      {min(latencies)*1000:.2f}ms")
        print(f"Max Latency:      {max(latencies)*1000:.2f}ms")
    print("\nStatus Codes Distribution:")
    for code, count in status_codes.items():
        print(f"  {code}: {count}")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwisterLab Async Load Tester")
    parser.add_argument("--url", default="http://localhost:8000/api/system/health", help="Target URL")
    parser.add_argument("-n", "--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("-c", "--concurrency", type=int, default=20, help="Concurrency limit")
    parser.add_argument("-t", "--token", default=None, help="Optional Bearer token for protected endpoints")
    
    args = parser.parse_args()
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(load_test(args.url, args.requests, args.concurrency, args.token))

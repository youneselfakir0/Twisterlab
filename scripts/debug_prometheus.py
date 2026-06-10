
import requests
import json
import sys

PROM_URL = "http://192.168.0.30:30090/api/v1/query"

def query_prometheus(query):
    print(f"Querying: {query}")
    try:
        resp = requests.get(PROM_URL, params={"query": query})
        data = resp.json()
        status = data.get("status")
        results = data.get("data", {}).get("result", [])
        
        print(f"Status: {status}")
        print(f"Result Count: {len(results)}")
        
        if len(results) > 0:
            print("Sample Data:")
            print(json.dumps(results[0], indent=2))
            return True
        else:
            print("No data found for query.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Check 1: Simple UP metric for mcp-unified
    print("--- Check 1: Custom App Metrics ---")
    query_prometheus('up{job="mcp-unified"}')
    
    # Check 2: cAdvisor Metric
    print("\n--- Check 2: Infrastructure Metrics (cAdvisor) ---")
    query_prometheus('container_cpu_usage_seconds_total{namespace="twisterlab"}')

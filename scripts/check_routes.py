import requests
import json

try:
    r = requests.get("http://192.168.0.30:30001/openapi.json")
    if r.status_code == 200:
        schema = r.json()
        paths = schema.get("paths", {}).keys()
        print("Available Routes:")
        for p in paths:
            print(p)
    else:
        print(f"Failed to get OpenAPI: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

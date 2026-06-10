import urllib.request
import json
import urllib.error

url = "http://127.0.0.1:18791/status"
headers = {
    "Authorization": "Bearer 63c37b514ddec59dcc754c874bcc9ad5a307a4cdd2604a67"
}

try:
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    print("Status code:", response.getcode())
    print("Response:", response.read().decode())
except urllib.error.URLError as e:
    print(f"Error connecting: {e}")
    if hasattr(e, 'read'):
        print(f"Error body: {e.read().decode()}")


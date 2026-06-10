import http.server
import http.client
import json
import os
import datetime

PORT = 8888
TARGET_HOST = "127.0.0.1"
TARGET_PORT = 8080
LOG_FILE = "proxy.log"

def logger(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")

class CommandCenterProxy(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy("GET")
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy("POST")
        else:
            self.send_error(404)

    def _proxy(self, method):
        # Ensure path rewriting is correct for /api prefix
        target_path = self.path[4:] # Strip /api
        if not target_path or target_path == "": target_path = "/"
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        logger(f"Proxying: {method} {target_path} | Size: {len(body)}")

        # Increased general timeout for agent/tool calls
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=120)
        try:
            # Reconstruct headers for target
            headers = {}
            for k, v in self.headers.items():
                if k.lower() not in ['host', 'connection', 'content-length']:
                    headers[k] = v
            
            if body:
                headers['Content-Length'] = str(len(body))
            
            # Special handling for metrics/tools
            if "/tools/" in target_path and method == "POST":
                headers['Content-Type'] = 'application/json'

            conn.request(method, target_path, body, headers)
            res = conn.getresponse()

            logger(f"Cluster Response: {res.status} for {target_path}")
            
            self.send_response(res.status)
            for k, v in res.getheaders():
                lk = k.lower()
                if lk not in ['content-encoding', 'transfer-encoding', 'content-length', 'access-control-allow-origin']:
                    self.send_header(k, v)
            
            response_data = res.read()
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data)
        except Exception as e:
            logger(f"CRITICAL PROXY ERROR: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {str(e)}".encode())
        finally:
            conn.close()

    def send_header(self, keyword, value):
        if keyword.lower() == 'access-control-allow-origin': return
        super().send_header(keyword, value)

if __name__ == "__main__":
    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
    logger(f"Command Center Proxy v2.2 (Ultra Debug Mode) starting...")
    server = http.server.HTTPServer(('0.0.0.0', PORT), CommandCenterProxy)
    server.serve_forever()

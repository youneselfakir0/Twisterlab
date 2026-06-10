import httpx
import json

BASE_URL = "http://192.168.0.30:30080"
HEADERS = {"Authorization": "Bearer dev-token-admin", "Content-Type": "application/json"}

def execute_command(cmd, timeout=30):
    print(f"Running: {cmd}")
    try:
        r = httpx.post(
            f"{BASE_URL}/tools/real-desktop-commander_execute_command",
            json={
                "arguments": {
                    "command": cmd,
                    "timeout": timeout
                }
            },
            headers=HEADERS,
            timeout=timeout+5
        )
        if r.status_code == 200:
            res = r.json()
            content = res.get("content", [{"text": "No content"}])[0].get("text")
            
            with open("disk_check.log", "a") as log:
                log.write(f"\n--- CMD: {cmd} ---\n")
            
            try:
                data = json.loads(content)
                with open("disk_check.log", "a") as log:
                    if "output" in data:
                        log.write(f"STDOUT:\n{data['output']}\n")
                        print(f"STDOUT: {data['output'][:50]}...")
                    if "stderr" in data and data['stderr']:
                        log.write(f"STDERR:\n{data['stderr']}\n")
            except:
                with open("disk_check.log", "a") as log:
                    log.write(f"OUTPUT: {content}\n")
        else:
            with open("disk_check.log", "a") as log:
                log.write(f"Error {r.status_code}: {r.text}\n")
    except Exception as e:
        print(f"Exception: {e}")

# Check disk usage
execute_command("df -h")
# Check largest directories in /var (typical culprit)
# Note: 'du' might not be in the whitelist of allowed commands! 
# Let's try ls -lh /var/log first as it is safer
# And maybe docker system usage if possible
execute_command("ls -lh /var/log")

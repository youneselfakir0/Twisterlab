import httpx
import json
import time

BASE_URL = "http://192.168.0.30:30080"
HEADERS = {"Authorization": "Bearer dev-token-admin", "Content-Type": "application/json"}

def run_maestro_task(task_description):
    print(f"MAESTRO: Received task -> '{task_description}'")
    print("Orchestrating agents... (this may take 10-20 seconds)")
    
    start_time = time.time()
    try:
        # Call maestro_orchestrate tool
        r = httpx.post(
            f"{BASE_URL}/tools/maestro_orchestrate",
            json={
                "arguments": {
                    "task": task_description,
                    "dry_run": False  # Let it actually execute commands like df -h
                }
            },
            headers=HEADERS,
            timeout=120  # Orchestration can be long
        )
        
        duration = time.time() - start_time
        
        if r.status_code == 200:
            res = r.json()
            
            # Extract content from MCP ToolResult
            content = res.get("content", [])
            if content and isinstance(content, list):
                result_text = content[0].get("text", "")
                
                # Check for error signature in text response
                if "Error" in result_text and "success" not in result_text.lower():
                     print(f"MAESTRO FAILED ({duration:.1f}s)")
                     print(result_text)
                else:
                    print(f"MAESTRO COMPLETED ({duration:.1f}s)")
                    
                    # Try to parse the text as JSON if it looks like it
                    try:
                        # Sometimes result is a JSON string inside the text
                        parsed = json.loads(result_text)
                        print(json.dumps(parsed, indent=2))
                    except:
                        # Otherwise print as text
                        print("\nRESULT:")
                        print(result_text)
            else:
                print(f"MAESTRO COMPLETED ({duration:.1f}s)")
                print(json.dumps(res, indent=2))
                
        else:
            print(f"API ERROR ({r.status_code})")
            print(r.text)
            
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    run_maestro_task("Analyze why the disk is almost full check large files")

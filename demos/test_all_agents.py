import requests
import json
import os
import time

# Use the IP detected from previous steps as default, but allow override
BASE_URL = os.getenv("TC_URL", "http://192.168.0.30:8081")
HEADERS = {
   "Content-Type": "application/json",
   "Authorization": "Bearer dev-token-admin" # Ensure we have admin access for all tools
}

def get_tools():
    try:
        print(f"🔍 Discovering tools at {BASE_URL}/tools...")
        resp = requests.get(f"{BASE_URL}/tools", headers=HEADERS, timeout=5)
        resp.raise_for_status()
        tools = resp.json()['tools']
        print(f"📋 Found {len(tools)} tools.")
        return tools
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return []

def run_test(tool_name, args):
    print(f"🧪 Testing tool: {tool_name}")
    print(f"   Input: {json.dumps(args)}")
    try:
        start_time = time.time()
        resp = requests.post(f"{BASE_URL}/tools/{tool_name}", json={"arguments": args}, headers=HEADERS, timeout=30)
        duration = time.time() - start_time
        
        if resp.status_code == 200:
            try:
                # Content is usually a list of text blocks in MCP
                content = resp.json().get('content', [])
                output = content[0]['text'] if content else "No content"
                # Truncate output if too long
                display_output = (output[:100] + '...') if len(str(output)) > 100 else output
                print(f"   ✅ Success ({duration:.2f}s): {display_output}")
            except:
                print(f"   ✅ Success ({duration:.2f}s): {resp.json()}")
        else:
            print(f"   ❌ Failed ({duration:.2f}s): {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print("-" * 60)

def main():
    tools = get_tools()
    
    # Define test payloads for known agents
    test_suite = {
        # Monitoring Agent
        "monitoring_health_check": {},
        "monitoring_get_system_metrics": {}, # Fixed: Removed invalid 'detailed' arg
        "monitoring_list_containers": {},
        "monitoring_get_container_logs": {"container_id": "twisterlab-demo-api", "tail": 10},
        "monitoring_get_llm_status": {},
        "monitoring_get_cache_stats": {},
        "monitoring_list_models": {},

        # Classifier Agent
        "real-classifier_classify_ticket": {"ticket_text": "The server is down and I cannot access the database."},
        
        # Sentiment Agent
        "sentiment-analyzer_analyze_sentiment": {"text": "TwisterLab is the best platform I have ever used! Great job."},
        
        # Backup Agent
        "real-backup_create_backup": {"service_name": "test_service_db"},
        "real-backup_list_backups": {},
        
        # Code Review Agent
        "code-review_analyze_code": {"code": "def login(user, password):\n    # TODO: fix this\n    print(password)"},
        "code-review_security_scan": {"code": "api_key = '12345-SECRET'"},
        
        # Resolver Agent
        "real-resolver_resolve_ticket": {"ticket_id": "TEST-101", "resolution_note": "Rebooted the server and verified connectivity."},
        
        # Database Agent
        "database_db_health": {},
        "database_list_tables": {},
        "database_describe_table": {"table_name": "agents"},
        "database_execute_query": {"query": "SELECT count(*) FROM agents"},
        
        # Cache Agent
        "cache_cache_keys": {"pattern": "*"},
        "cache_cache_stats": {},
        "cache_cache_set": {"key": "demo_test_key", "value": "test_value"},
        "cache_cache_get": {"key": "demo_test_key"},
        
        # Maestro (Orchestrator)
        "maestro_orchestrate": {"task": "Analyze the sentiment of 'I am happy'"},
        "maestro_list_agents": {},
        "maestro_chat": {"message": "Hello Maestro"},
        
        # Desktop Commander
        "real-desktop-commander_execute_command": {
            "device_id": "demo-pc-01", 
            "command": "echo 'Hello World'"
        },
        
        # Browser Agent
        "browser_browse": {
            "url": "http://example.com", 
            "screenshot": True
        },
    }
    
    print("\n🚀 STARTING AGENT SWARM TEST\n" + "="*60)
    
    # 1. Run defined tests for existing tools
    tested_count = 0
    for tool in tools:
        name = tool['name']
        if name in test_suite:
            run_test(name, test_suite[name])
            tested_count += 1
    
    # 2. Report coverage
    print(f"\n📊 TEST COMPLETE")
    print(f"   Tools Available: {len(tools)}")
    print(f"   Tools Tested:    {tested_count}")
    
    if tested_count < len(tools):
        print("\n⚠️  Untested Tools:")
        for tool in tools:
            if tool['name'] not in test_suite:
                print(f"   - {tool['name']}")

if __name__ == "__main__":
    main()

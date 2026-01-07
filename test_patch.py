import asyncio
import sys
import logging

# Configure logging to see what happens
logging.basicConfig(level=logging.INFO)

# Force python path
sys.path.append("/app/src")

async def main():
    print("--- 1. Testing System Clients ---")
    try:
        from twisterlab.services.system_client import DockerSystemClient
        from twisterlab.services.postgres_client import PostgresClient
        
        dc = DockerSystemClient()
        print("✅ DockerSystemClient Instantiated")
        
        pc = PostgresClient()
        print("✅ PostgresClient Instantiated")
    except Exception as e:
        print(f"❌ Client Instantiation Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- 2. Testing Maestro Chat ---")
    try:
        from twisterlab.agents.core.maestro_agent import MaestroAgent
        
        agent = MaestroAgent()
        print("Invoking handle_chat('hello')...")
        
        # This calls CortexClient behind the scenes
        # If 'dict' error is present, it will crash here.
        # If network error (LLM unreachable), it will return AgentResponse with success=False but NO crash.
        result = await agent.handle_chat("hello", model="qwen3:8b")
        
        print(f"Chat Result: {result}")
        
        if result.success:
            print("✅ Chat Success")
        else:
            print(f"⚠️ Chat Failed (expected if no LLM), Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Maestro Chat Crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

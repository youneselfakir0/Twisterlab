import asyncio
import logging
import sys
from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_coordinated_review():
    print("--- Phase 20: Validation Audit ---")
    agent = RealCodeReviewAgent()
    
    # Default snippet if no file provided
    code_to_test = """
import os
import twisterlab.api.main

def risky_function(data):
    api_key = "sk-live-12345" 
    eval(data)
    try:
        pass
    except:
        pass
"""
    filename = "risky_module.py"

    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        with open(target_file, "r") as f:
            code_to_test = f.read()
        filename = target_file
        print(f"Testing external file: {filename}")

    print("Launching deep audit...")
    res = await agent.handle_deep_audit(code_to_test, filename=filename)
    
    if res.success:
        print("OK: Orchestrated analysis completed.")
        print(f"Findings ({res.data['findings_count']}):")
        for f in res.data['findings']:
            print(f"- [{f['agent'].upper()}] {f['severity'].upper()}: {f['message']}")
    else:
        print(f"ERROR: Analysis failed: {res.error}")

if __name__ == "__main__":
    asyncio.run(test_coordinated_review())

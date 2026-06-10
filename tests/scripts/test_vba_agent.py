import asyncio
import logging
import json
from twisterlab.agents.real.real_vba_expert_agent import RealVbaExpertAgent

logging.basicConfig(level=logging.ERROR)

async def main():
    agent = RealVbaExpertAgent()
    
    print("\n=========== TESTING VBA ANALYSIS ===========")
    code = """
Sub Testmacro()
    Range("A1").Select
    Selection.Value = "Hello"
    On Error Resume Next
    Dim x As Integer
    x = 1 / 0
End Sub
    """
    resp2 = await agent.handle_analyze_vba(code)
    print("Issues Found:", json.dumps(resp2.data["issues"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())

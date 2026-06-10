import asyncio
import os
import sys
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent, TaskCategory, TaskPriority

async def test_maestro_repair_logic():
    print("--- Testing Maestro Self-Correction (Repair) ---")
    
    agent = RealMaestroAgent()
    agent._ollama_url = "http://mock-ollama"
    agent._use_llm = True
    
    # Mock task and context
    task = "Verify database health"
    
    # Mock first response as INVALID (missing keys)
    # Mock second response as VALID
    invalid_resp = {"response": json.dumps({"category": "database"})} # Missing priority, suggested_requirements
    valid_resp = {"response": json.dumps({
        "category": "database", 
        "priority": "high", 
        "suggested_requirements": ["db_health"],
        "keywords": ["db"]
    })}
    
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json = lambda: invalid_resp
    
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json = lambda: valid_resp
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = [mock_response_1, mock_response_2]
        
        print("[INFO] Attempting LLM analysis with simulated first-try failure...")
        result = await agent._llm_analyze(task, None)
        
        if result and result["category"] == TaskCategory.DATABASE and result["priority"] == TaskPriority.HIGH:
            print("[OK] Maestro successfully repaired the analysis JSON on second attempt.")
        else:
            print(f"[FAIL] Maestro failed to repair analysis. Result: {result}")
            
        if mock_post.call_count == 2:
            print("[OK] Exactly 2 calls were made (1 original + 1 repair).")
        else:
            print(f"[FAIL] Expected 2 calls, got {mock_post.call_count}")

async def test_maestro_fallback_after_repair_failed():
    print("\n--- Testing Maestro Fallback after Repair Failure ---")
    
    agent = RealMaestroAgent()
    agent._ollama_url = "http://mock-ollama"
    agent._use_llm = True
    
    # Mock both responses as INVALID
    invalid_resp = {"response": "This is not even JSON"}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: invalid_resp
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response
        
        print("[INFO] Attempting LLM analysis with simulated total failure...")
        result = await agent._llm_analyze("Critical database crash", None)
        
        if result is None:
            print("[OK] Maestro correctly returned None (triggering rule-based fallback).")
        else:
            print(f"[FAIL] Maestro should have returned None for total failure. Got: {result}")

if __name__ == "__main__":
    asyncio.run(test_maestro_repair_logic())
    asyncio.run(test_maestro_fallback_after_repair_failed())

#!/usr/bin/env python
"""Test Maestro on EdgeServer"""
import asyncio
from twisterlab.agents.registry import agent_registry

async def test_maestro():
    maestro = agent_registry.get_agent("maestro")
    print(f"Maestro: {maestro.name}")
    print(f"Description: {maestro.description}")
    print(f"Capabilities: {[c.name for c in maestro.get_capabilities()]}")
    
    # Test analyze_task
    result = await maestro.execute("analyze_task", task="Database is slow")
    print(f"\nAnalyze result: {result}")
    
    # Test orchestrate (dry_run)
    result = await maestro.execute("orchestrate", task="Database is slow", context={}, dry_run=True)
    print(f"\nOrchestrate result: {result}")

if __name__ == "__main__":
    asyncio.run(test_maestro())

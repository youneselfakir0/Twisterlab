#!/usr/bin/env python3
"""
Simple validation script to test OpenTelemetry tracing implementation
in TwisterLab agents.
"""

import asyncio
import sys
import os

# Add src to path so we can import twisterlab modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from twisterlab.agents.base.base_agent import BaseAgent
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


class TestAgent(BaseAgent):
    """Test agent to verify tracing works"""
    operation_name = "test_operation"
    
    async def _process(self, context):
        # Simulate some work
        await asyncio.sleep(0.01)
        return {"result": "success", "input": context}


async def test_tracing():
    # Set up in-memory tracer for testing
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    
    # Create and run test agent
    agent = TestAgent()
    result = await agent.run({"test": "data"})
    
    # Check results
    assert result["result"] == "success"
    assert result["input"]["test"] == "data"
    
    # Check spans
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    
    span = spans[0]
    assert span.name == "TestAgent.test_operation"
    assert span.attributes["agent.id"] == agent.agent_id
    assert span.attributes["agent.name"] == "TestAgent"
    assert span.attributes["agent.version"] == "1.0"
    assert span.status.status_code == trace.StatusCode.OK
    
    print("✓ Tracing validation passed!")
    print(f"  - Span name: {span.name}")
    print(f"  - Agent ID: {span.attributes['agent.id']}")
    print(f"  - Agent name: {span.attributes['agent.name']}")
    print(f"  - Status: {span.status.status_code}")
    
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_tracing())
        print("\n✅ All tracing validations passed!")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)
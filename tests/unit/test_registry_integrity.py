import pytest
from twisterlab.agents.registry import AgentRegistry, get_agent_registry

def test_registry_capabilities_resolvable():
    """Registry Integrity: Every statically declared capability must resolve back to an agent."""
    registry = get_agent_registry()
    agents_meta = registry.list_agents()
    
    unique_capabilities = set()
    for meta in agents_meta.values():
        unique_capabilities.update(meta.get("capabilities", []))
    
    errors = []
    for cap in unique_capabilities:
        resolved_key = registry.find_agent_by_capability(cap)
        if not resolved_key:
            errors.append(f"Capability '{cap}' declared but not resolvable via find_agent_by_capability.")
        elif resolved_key not in agents_meta:
            errors.append(f"Capability '{cap}' resolved to unknown agent key '{resolved_key}'.")
            
    if errors:
        pytest.fail("Registry Integrity Failed:\n" + "\n".join(errors))

def test_registry_precedence():
    """Registry Integrity: Highest priority wins, lexical tiebreaker."""
    # We'll use a local registry instance to avoid polluting the global one
    registry = AgentRegistry()
    # Reset it (since it's a singleton in the implementation we need to be careful, 
    # but for this test we'll just check existing fleet known priorities)
    
    # CASE 1: Cortex (20) vs others
    # 'chat' is claimed by cortex
    assert registry.find_agent_by_capability("chat") == "cortex"
    
    # CASE 2: archive_result (20) vs others
    assert registry.find_agent_by_capability("archive_result") == "archive"

    # CASE 3: Lexical Tiebreaker
    # Register two agents with same priority and same capability
    def dummy_factory(): return None
    registry.register_agent("agent-b", dummy_factory, capabilities=["shared_cap"], priority=50)
    registry.register_agent("agent-a", dummy_factory, capabilities=["shared_cap"], priority=50)
    
    # agent-a should win because it's lexically first
    assert registry.find_agent_by_capability("shared_cap") == "agent-a"
    
    # CASE 4: Priority victory
    registry.register_agent("agent-high", dummy_factory, capabilities=["shared_cap"], priority=100)
    assert registry.find_agent_by_capability("shared_cap") == "agent-high"

def test_registry_missing_resolutions():
    """Registry Integrity: Fails gracefully for unknown capabilities."""
    registry = get_agent_registry()
    assert registry.find_agent_by_capability("non_existent_capability_123") is None

if __name__ == "__main__":
    pytest.main([__file__])

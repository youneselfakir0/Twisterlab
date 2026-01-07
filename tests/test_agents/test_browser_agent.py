import pytest
from twisterlab.agents.real.browser_agent import RealBrowserAgent


@pytest.mark.unit
def test_browser_agent_initialization():
    """Test RealBrowserAgent can be instantiated."""
    agent = RealBrowserAgent()
    assert agent is not None
    assert agent.name == "browser"


@pytest.mark.unit
def test_browser_agent_properties():
    """Test RealBrowserAgent has expected properties."""
    agent = RealBrowserAgent()
    assert agent.description is not None
    assert len(agent.get_capabilities()) > 0


@pytest.mark.unit
def test_browser_agent_capabilities():
    """Test RealBrowserAgent has browse capability."""
    agent = RealBrowserAgent()
    caps = agent.get_capabilities()
    cap_names = [c.name for c in caps]
    assert "browse" in cap_names

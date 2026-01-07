import pytest

from twisterlab.agents.real.browser_agent import BrowserAgent


@pytest.fixture
def browser_agent():
    return BrowserAgent()


def test_browser_agent_initialization(browser_agent):
    assert browser_agent is not None


def test_browser_agent_functionality(browser_agent):
    # Verify the agent's execute_tool behavior
    result = browser_agent.execute_tool(
        "create_browser_tool", {"target_url": "https://example.com"}
    )
    assert result is not None
    assert isinstance(result, dict)
    assert result.get("status") == "success"


def test_browser_agent_error_handling(browser_agent):
    # Verify invalid URL yields an error result
    result = browser_agent.execute_tool(
        "create_browser_tool", {"target_url": "invalid_url"}
    )
    assert result.get("status") == "error"

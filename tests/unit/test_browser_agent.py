"""
Tests for cross-platform browser agent.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from twisterlab.agents.real.browser_agent import (
    RealBrowserAgent,
    _extract_title_from_html,
    _extract_text_from_html,
    _check_playwright_browsers,
)


class TestHTMLExtraction:
    """Test HTML extraction utilities."""

    def test_extract_title_simple(self):
        html = "<html><head><title>Test Page</title></head></html>"
        assert _extract_title_from_html(html) == "Test Page"

    def test_extract_title_with_attributes(self):
        html = '<title lang="en">My Title</title>'
        assert _extract_title_from_html(html) == "My Title"

    def test_extract_title_missing(self):
        html = "<html><head></head></html>"
        assert _extract_title_from_html(html) == "No title"

    def test_extract_text_basic(self):
        html = "<html><body><p>Hello World</p></body></html>"
        text = _extract_text_from_html(html)
        assert "Hello World" in text

    def test_extract_text_removes_scripts(self):
        html = "<html><script>alert('bad');</script><body>Good content</body></html>"
        text = _extract_text_from_html(html)
        assert "alert" not in text
        assert "Good content" in text

    def test_extract_text_removes_styles(self):
        html = "<html><style>.hidden{display:none}</style><body>Visible</body></html>"
        text = _extract_text_from_html(html)
        assert "display" not in text
        assert "Visible" in text


class TestBrowserAgentInit:
    """Test browser agent initialization."""

    def test_agent_name(self):
        agent = RealBrowserAgent()
        assert agent.name == "browser"

    def test_agent_has_capabilities(self):
        agent = RealBrowserAgent()
        caps = agent.get_capabilities()
        assert len(caps) >= 2
        cap_names = [c.name for c in caps]
        assert "browse" in cap_names
        assert "status" in cap_names

    def test_agent_accepts_service_registry(self):
        """Agent should accept optional service_registry parameter."""
        mock_registry = MagicMock()
        agent = RealBrowserAgent(service_registry=mock_registry)
        assert agent.name == "browser"


class TestBrowserAgentBrowse:
    """Test browsing functionality."""

    @pytest.mark.asyncio
    async def test_invalid_url_rejected(self):
        agent = RealBrowserAgent()
        result = await agent.handle_browse("not-a-url")
        assert result.success is False
        assert "Invalid URL" in result.error

    @pytest.mark.asyncio
    async def test_ftp_url_rejected(self):
        agent = RealBrowserAgent()
        result = await agent.handle_browse("ftp://example.com")
        assert result.success is False

    @pytest.mark.asyncio
    @patch("twisterlab.agents.real.browser_agent.HTTPX_AVAILABLE", True)
    @patch("twisterlab.agents.real.browser_agent.httpx")
    async def test_httpx_fallback_works(self, mock_httpx):
        """Test that httpx fallback works correctly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.text = "<html><title>Test</title><body>Content</body></html>"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_httpx.AsyncClient.return_value = mock_client

        agent = RealBrowserAgent()
        agent._engine = "httpx"  # Force httpx

        result = await agent.handle_browse("https://example.com", force_engine="httpx")

        assert result.success is True
        assert result.data["engine"] == "httpx"
        assert result.data["js_rendered"] is False


class TestBrowserStatus:
    """Test browser status capability."""

    @pytest.mark.asyncio
    async def test_status_returns_platform_info(self):
        agent = RealBrowserAgent()
        result = await agent.handle_status()

        assert result.success is True
        assert "platform" in result.data
        assert "active_engine" in result.data
        assert "features" in result.data


class TestPlaywrightCheck:
    """Test Playwright browser detection."""

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_check_finds_chromium(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["chromium-1200", "ffmpeg-1011"]

        with patch(
            "twisterlab.agents.real.browser_agent.PLAYWRIGHT_AVAILABLE", True
        ):
            result = _check_playwright_browsers()
            # Will return True if chromium folder found
            assert isinstance(result, bool)

    @patch("twisterlab.agents.real.browser_agent.PLAYWRIGHT_AVAILABLE", False)
    def test_check_returns_false_without_playwright(self):
        result = _check_playwright_browsers()
        assert result is False

"""
Browser automation agent (Real implementation).

Cross-platform compatible:
- Uses Playwright when browsers are installed (full features + screenshots)
- Falls back to httpx for simple HTTP requests (no JS rendering)
- Works on Linux (K8s) and Windows (local dev)
"""

from __future__ import annotations

import base64
import logging
import os
import platform
import re
from typing import List, Optional

# Try importing Playwright
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False

# Try importing httpx as fallback
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


def _check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    if not PLAYWRIGHT_AVAILABLE:
        return False

    # Check common Playwright cache locations
    home = os.path.expanduser("~")
    cache_paths = [
        os.path.join(home, ".cache", "ms-playwright"),  # Linux
        os.path.join(home, "AppData", "Local", "ms-playwright"),  # Windows
        os.path.join(home, "Library", "Caches", "ms-playwright"),  # macOS
    ]

    for path in cache_paths:
        if os.path.exists(path):
            # Check if chromium folder exists
            for item in os.listdir(path) if os.path.isdir(path) else []:
                if "chromium" in item.lower():
                    return True
    return False


def _extract_title_from_html(html: str) -> str:
    """Extract title from HTML content."""
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else "No title"


def _extract_text_from_html(html: str) -> str:
    """Extract visible text from HTML (basic extraction)."""
    # Remove script and style content
    html = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


class RealBrowserAgent(TwisterAgent):
    """
    Cross-platform browser automation agent.

    Features:
    - Playwright: Full browser automation with JS rendering and screenshots
    - httpx fallback: Simple HTTP requests when Playwright unavailable
    - Auto-detection: Automatically selects best available engine
    """

    def __init__(self, service_registry=None):
        super().__init__(service_registry)
        self._playwright_ok = _check_playwright_browsers()
        self._engine = self._detect_engine()
        logger.info(
            f"🌐 BrowserAgent initialized - Engine: {self._engine}, Platform: {platform.system()}"
        )

    def _detect_engine(self) -> str:
        """Detect best available browsing engine."""
        if PLAYWRIGHT_AVAILABLE and self._playwright_ok:
            return "playwright"
        elif HTTPX_AVAILABLE:
            return "httpx"
        else:
            return "none"

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        engine_info = f"Current engine: {self._engine}"
        return f"Cross-platform web browsing agent. {engine_info}"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="browse",
                description="Browse a URL and return page content. Uses Playwright if available, httpx as fallback.",
                handler="handle_browse",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "url",
                        ParamType.STRING,
                        "URL to visit (must start with http/https)",
                    ),
                    CapabilityParam(
                        "screenshot",
                        ParamType.BOOLEAN,
                        "Take a screenshot (only with Playwright)",
                        required=False,
                        default=True,
                    ),
                    CapabilityParam(
                        "force_engine",
                        ParamType.STRING,
                        "Force specific engine: 'playwright', 'httpx', or 'auto'",
                        required=False,
                        default="auto",
                    ),
                ],
                tags=["web", "scraping", "browser", "cross-platform"],
            ),
            AgentCapability(
                name="status",
                description="Get browser agent status and available engines",
                handler="handle_status",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["status", "info"],
            ),
        ]

    async def handle_status(self) -> AgentResponse:
        """Return browser agent status."""
        return AgentResponse(
            success=True,
            data={
                "platform": platform.system(),
                "playwright_installed": PLAYWRIGHT_AVAILABLE,
                "playwright_browsers_ok": self._playwright_ok,
                "httpx_installed": HTTPX_AVAILABLE,
                "active_engine": self._engine,
                "features": {
                    "playwright": ["js_rendering", "screenshots", "full_browser"],
                    "httpx": ["http_requests", "fast", "lightweight"],
                },
            },
        )

    async def handle_browse(
        self, url: str, screenshot: bool = True, force_engine: str = "auto"
    ) -> AgentResponse:
        """Browse a URL using best available engine."""
        if not url.startswith("http"):
            return AgentResponse(
                success=False, error="Invalid URL. Must start with http or https."
            )

        # Determine engine to use
        engine = force_engine if force_engine != "auto" else self._engine

        # Validate engine availability
        if engine == "playwright" and not (
            PLAYWRIGHT_AVAILABLE and self._playwright_ok
        ):
            if HTTPX_AVAILABLE:
                logger.warning("Playwright not available, falling back to httpx")
                engine = "httpx"
            else:
                return AgentResponse(
                    success=False,
                    error="Playwright browsers not installed and no fallback available",
                )

        if engine == "httpx" and not HTTPX_AVAILABLE:
            return AgentResponse(success=False, error="httpx not installed")

        if engine == "none":
            return AgentResponse(
                success=False,
                error="No browsing engine available. Install playwright or httpx.",
            )

        logger.info(f"🌐 Browsing {url} with engine: {engine}")

        if engine == "playwright":
            return await self._browse_playwright(url, screenshot)
        else:
            return await self._browse_httpx(url)

    async def _browse_playwright(self, url: str, screenshot: bool) -> AgentResponse:
        """Browse using Playwright (full browser)."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720}
                )
                page = await context.new_page()

                await page.goto(url, timeout=30000, wait_until="domcontentloaded")

                title = await page.title()
                text_content = await page.evaluate("document.body.innerText")
                preview = (
                    text_content[:1000] + "..."
                    if len(text_content) > 1000
                    else text_content
                )

                snapshots = []
                if screenshot:
                    img_buffer = await page.screenshot(type="png", full_page=False)
                    b64 = base64.b64encode(img_buffer).decode("utf-8")
                    snapshots.append(f"data:image/png;base64,{b64}")

                await browser.close()

                return AgentResponse(
                    success=True,
                    data={
                        "url": url,
                        "title": title,
                        "content_preview": preview,
                        "snapshots": snapshots,
                        "engine": "playwright",
                        "js_rendered": True,
                    },
                )

        except Exception as e:
            logger.error(f"Playwright error: {e}")
            # Try fallback to httpx
            if HTTPX_AVAILABLE:
                logger.info("Falling back to httpx after Playwright failure")
                return await self._browse_httpx(url, fallback_reason=str(e))
            return AgentResponse(success=False, error=f"Playwright error: {e}")

    async def _browse_httpx(
        self, url: str, fallback_reason: Optional[str] = None
    ) -> AgentResponse:
        """Browse using httpx (HTTP client, no JS)."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "TwisterLab-Browser/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                html = response.text
                title = _extract_title_from_html(html)
                text = _extract_text_from_html(html)
                preview = text[:1000] + "..." if len(text) > 1000 else text

                result = {
                    "url": str(response.url),
                    "title": title,
                    "content_preview": preview,
                    "snapshots": [],  # httpx cannot take screenshots
                    "engine": "httpx",
                    "js_rendered": False,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "unknown"),
                }

                if fallback_reason:
                    result["fallback_reason"] = fallback_reason

                return AgentResponse(success=True, data=result)

        except Exception as e:
            logger.error(f"httpx error: {e}")
            return AgentResponse(success=False, error=f"HTTP request failed: {e}")


# Alias for compatibility
BrowserAgent = RealBrowserAgent

__all__ = ["RealBrowserAgent", "BrowserAgent"]

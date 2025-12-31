"""
Browser automation agent (Real implementation).
Uses Playwright to browse web pages and capture screenshots.
"""

from __future__ import annotations

import base64
import logging
from typing import List

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None # Handle missing dependency gracefully

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class RealBrowserAgent(TwisterAgent):
    """
    Performs real browser automation using Playwright.
    """

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Performs real web browsing, scraping and screenshots using Playwright"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="browse",
                description="Browse a URL, return title/text and optionally a screenshot",
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
                        "Take a screenshot",
                        required=False,
                        default=True,
                    ),
                ],
                tags=["web", "scraping", "browser", "playwright"],
            )
        ]

    async def handle_browse(self, url: str, screenshot: bool = True) -> AgentResponse:
        """Browse a URL using Playwright."""
        if not url.startswith("http"):
            return AgentResponse(success=False, error="Invalid URL. Must start with http or https.")
        
        if not async_playwright:
            return AgentResponse(success=False, error="Playwright is not installed. Run 'pip install playwright' and 'playwright install'.")

        logger.info(f"🚀 RealBrowserAgent visiting: {url}")
        
        try:
            async with async_playwright() as p:
                # Launch browser (chromium)
                browser = await p.chromium.launch(headless=True)
                # Create context with viewport
                context = await browser.new_context(viewport={"width": 1280, "height": 720})
                page = await context.new_page()
                
                # Navigation
                logger.debug("Navigating...")
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                # Extract data
                title = await page.title()
                # Get text content (stripped limit)
                text_content = await page.evaluate("document.body.innerText")
                preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
                
                snapshots = []
                if screenshot:
                    logger.debug("Taking screenshot...")
                    request_buffer = await page.screenshot(type="png", full_page=False)
                    b64 = base64.b64encode(request_buffer).decode("utf-8")
                    snapshots.append(f"data:image/png;base64,{b64}")
                
                await browser.close()
                
                return AgentResponse(
                    success=True,
                    data={
                        "url": url,
                        "title": title,
                        "content_preview": preview,
                        "snapshots": snapshots,
                        "engine": "playwright"
                    },
                )

        except Exception as e:
            logger.error(f"Browser error: {e}")
            return AgentResponse(success=False, error=str(e))


__all__ = ["RealBrowserAgent"]

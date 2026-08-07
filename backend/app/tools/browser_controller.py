import re
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# Prompt Injection Attack Patterns
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)disregard\s+(all\s+)?previous\s+instructions",
    r"(?i)you\s+are\s+now\s+a\b",
    r"(?i)system\s*prompt\s*:",
    r"(?i)act\s+as\s+an?\s+unrestricted",
    r"(?i)override\s+(all\s+)?safety\s+rules",
    r"(?i)jailbreak\s+activated",
]


class PlaywrightBrowserTool:
    """
    Playwright Browser Automation module featuring headless page navigation, PDF extraction,
    and a Prompt-Injection Shielding Layer that sanitizes untrusted web text and wraps it in 
    explicit security boundary tags: <untrusted_web_data url="...">.
    """

    def __init__(self, timeout_ms: int = 15000):
        self.timeout_ms = timeout_ms
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AURA-Research-Agent/1.0"

    def sanitize_text(self, text_input: str) -> str:
        """
        Prompt-Injection Shielding Layer:
        Strips out prompt injection overrides and malicious instruction patterns.
        """
        sanitized = text_input
        for pattern in PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[BLOCKED_PROMPT_INJECTION_ATTEMPT]", sanitized)
        return sanitized

    def wrap_untrusted_data(self, url: str, raw_text: str) -> str:
        """Wrap extracted web content in explicit untrusted data security boundaries."""
        sanitized = self.sanitize_text(raw_text)
        return f'<untrusted_web_data url="{url}">\n{sanitized}\n</untrusted_web_data>'

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Launch Playwright headless browser, set strict user-agent and 15s timeout,
        extract page title, inner text, links, PDF download links, and apply prompt-injection shielding.
        """
        start_time = time.time()
        
        # Try Playwright Async API
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = None
                try:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(user_agent=self.user_agent)
                    page = await context.new_page()
                    page.set_default_navigation_timeout(self.timeout_ms)

                    response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    title = await page.title()
                    inner_text = await page.inner_text("body")

                    # Extract all href links and filter PDF downloads
                    links = await page.eval_on_selector_all(
                        "a[href]", "elements => elements.map(e => e.href)"
                    )
                    pdf_links = [link for link in links if link.lower().endswith(".pdf")]

                    shielded_text = self.wrap_untrusted_data(url, inner_text)

                    return {
                        "url": url,
                        "title": title,
                        "sanitized_text": shielded_text,
                        "raw_text": inner_text[:1000],
                        "links": links[:20],
                        "pdf_links": pdf_links,
                        "status": "SUCCESS",
                        "response_code": response.status if response else 200,
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                finally:
                    if browser:
                        await browser.close()

        except Exception as playwright_err:
            logger.warning(f"Playwright browser scrape warning: {playwright_err}. Executing HTTPX fallback...")
            return await self._scrape_url_httpx_fallback(url, start_time)

    async def _scrape_url_httpx_fallback(self, url: str, start_time: float) -> Dict[str, Any]:
        """Fallback web scraper using HTTPX if Playwright browser binary is uninstalled."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {"User-Agent": self.user_agent}
                resp = await client.get(url, headers=headers)
                
                title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
                title = title_match.group(1) if title_match else "Web Page"

                # Strip HTML tags
                raw_text = re.sub(r"<[^>]+>", " ", resp.text)
                raw_text = re.sub(r"\s+", " ", raw_text).strip()

                links = re.findall(r'href=["\'](https?://[^\s"\']+)["\']', resp.text)
                pdf_links = [l for l in links if l.lower().endswith(".pdf")]

                shielded_text = self.wrap_untrusted_data(url, raw_text)

                return {
                    "url": url,
                    "title": title,
                    "sanitized_text": shielded_text,
                    "raw_text": raw_text[:1000],
                    "links": links[:20],
                    "pdf_links": pdf_links,
                    "status": "SUCCESS_FALLBACK",
                    "response_code": resp.status_code,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            logger.error(f"Scraper error for {url}: {e}")
            empty_shielded = self.wrap_untrusted_data(url, f"Failed to fetch content: {str(e)}")
            return {
                "url": url,
                "title": "Error Page",
                "sanitized_text": empty_shielded,
                "raw_text": "",
                "links": [],
                "pdf_links": [],
                "status": "ERROR",
                "response_code": 500,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

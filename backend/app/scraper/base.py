"""Shared utilities for scraper modules."""
from __future__ import annotations

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = structlog.get_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
]


def backoff_delay(attempt: int, base: float = 1.5, jitter: float = 0.2) -> float:
    """Return exponential backoff with jitter."""

    delay = base ** attempt
    return delay + random.uniform(-jitter, jitter)


async def polite_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Randomized delay to reduce blocking risk."""

    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


@dataclass
class Snapshot:
    """Metadata for saved HTML or screenshot artifacts."""

    url: str
    fetched_at: float
    html_path: Optional[Path] = None
    screenshot_path: Optional[Path] = None


def ensure_storage_path(base_dir: Path, *segments: str) -> Path:
    """Create directories for storing scraper outputs."""

    target = base_dir.joinpath(*segments)
    target.mkdir(parents=True, exist_ok=True)
    return target


@asynccontextmanager
async def browser_context(*, headless: bool = True, user_agent: Optional[str] = None) -> AsyncIterator[BrowserContext]:
    """Yield a Playwright browser context with randomized user-agent."""

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent=user_agent or random.choice(USER_AGENTS))
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


async def capture_page(
    context: BrowserContext,
    url: str,
    *,
    wait_until: str = "networkidle",
    screenshot: bool = False,
    storage_dir: Optional[Path] = None,
    timeout: int = 30_000,
) -> Snapshot:
    """Navigate to a page and capture HTML (and optionally a screenshot)."""

    page: Page = await context.new_page()
    await page.goto(url, wait_until=wait_until, timeout=timeout)
    await polite_delay(1.5, 3.5)

    html = await page.content()
    fetched_at = time.time()
    html_path: Optional[Path] = None
    screenshot_path: Optional[Path] = None

    if storage_dir:
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(fetched_at)
        html_path = storage_dir / f"snapshot_{timestamp}.html"
        html_path.write_text(html, encoding="utf-8")
        if screenshot:
            screenshot_path = storage_dir / f"snapshot_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

    await page.close()
    return Snapshot(url=url, fetched_at=fetched_at, html_path=html_path, screenshot_path=screenshot_path)


async def run_with_retries(coro_factory, *, attempts: int = 3) -> Optional[Snapshot]:
    """Retry helper for capture tasks."""

    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001 - we want broad logging
            logger.warning("scraper.retry", attempt=attempt, error=str(exc))
            await asyncio.sleep(backoff_delay(attempt))
    logger.error("scraper.failed", attempts=attempts)
    return None


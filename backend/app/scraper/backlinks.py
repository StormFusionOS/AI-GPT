"""Backlinks scraper that discovers referring domains and captures context."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import structlog
from bs4 import BeautifulSoup

from .base import Snapshot, browser_context, capture_page, ensure_storage_path, polite_delay, run_with_retries

logger = structlog.get_logger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search?q={query}&num=10&hl=en"


def parse_serp_backlinks(html: str, domain: str) -> List[Dict[str, Any]]:
    """Extract backlink candidate URLs from Google SERP HTML."""

    soup = BeautifulSoup(html, "lxml")
    entries = []
    for result in soup.select("div.g"):
        link = result.select_one("a")
        if not link:
            continue
        url = link.get("href")
        if not url or domain in url:
            continue
        title = result.select_one("h3")
        snippet = result.select_one("div.VwiC3b")
        entries.append(
            {
                "url": url,
                "title": title.get_text(strip=True) if title else "",
                "snippet": snippet.get_text(strip=True) if snippet else "",
            }
        )
    return entries


async def scrape_backlinks(
    *,
    domain: str,
    storage_dir: Path,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Perform a Google search for backlinks and capture referring pages."""

    query = f"link:{domain}".replace("://", " ")
    results: List[Dict[str, Any]] = []
    serp_dir = ensure_storage_path(storage_dir, "backlinks", "serp")

    async with browser_context() as context:
        async def _fetch_serp() -> Snapshot:
            return await capture_page(context, GOOGLE_SEARCH_URL.format(query=query), storage_dir=serp_dir)

        serp_snapshot = await run_with_retries(_fetch_serp)
        if serp_snapshot is None or serp_snapshot.html_path is None:
            return results

        html = serp_snapshot.html_path.read_text(encoding="utf-8")
        candidates = parse_serp_backlinks(html, domain)

        for candidate in candidates[:max_results]:
            referer_dir = ensure_storage_path(storage_dir, "backlinks", "pages")

            async def _fetch_candidate() -> Snapshot:
                return await capture_page(
                    context,
                    candidate["url"],
                    storage_dir=referer_dir,
                    screenshot=True,
                    wait_until="domcontentloaded",
                )

            snapshot = await run_with_retries(_fetch_candidate)
            if snapshot is None or snapshot.html_path is None:
                continue

            html = snapshot.html_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "lxml")
            anchor = soup.find("a", href=lambda href: href and domain in href)
            surrounding_text = anchor.find_parent("p").get_text(strip=True) if anchor else ""
            candidate.update(
                {
                    "anchor_text": anchor.get_text(strip=True) if anchor else "",
                    "context": surrounding_text,
                    "screenshot_path": str(snapshot.screenshot_path) if snapshot.screenshot_path else None,
                }
            )
            results.append(candidate)
            await polite_delay()

    (storage_dir / "backlinks_summary.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    return results


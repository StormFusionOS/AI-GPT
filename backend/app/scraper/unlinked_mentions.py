"""Scraper that looks for brand mentions without backlinks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import structlog
from bs4 import BeautifulSoup

from .base import Snapshot, browser_context, capture_page, ensure_storage_path, polite_delay, run_with_retries

logger = structlog.get_logger(__name__)

MENTION_QUERY = "\"{brand}\" -site:{domain}"


def parse_unlinked_mentions(html: str, domain: str) -> List[Dict[str, str]]:
    """Return SERP entries that mention the brand but lack backlinks."""

    soup = BeautifulSoup(html, "lxml")
    mentions: List[Dict[str, str]] = []
    for result in soup.select("div.g"):
        link = result.select_one("a")
        if not link:
            continue
        url = link.get("href")
        snippet = result.select_one("div.VwiC3b")
        snippet_text = snippet.get_text(strip=True) if snippet else ""
        if domain in snippet_text:
            continue
        mentions.append(
            {
                "url": url,
                "snippet": snippet_text,
            }
        )
    return mentions


async def scrape_unlinked_mentions(
    *,
    brand: str,
    domain: str,
    storage_dir: Path,
) -> List[Dict[str, str]]:
    """Query Google for brand mentions that lack direct backlinks."""

    query = MENTION_QUERY.format(brand=brand, domain=domain)
    directory = ensure_storage_path(storage_dir, "unlinked_mentions", brand.replace(" ", "_"))

    async with browser_context() as context:
        async def _fetch() -> Snapshot:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return await capture_page(context, url, storage_dir=directory)

        snapshot = await run_with_retries(_fetch)
        if snapshot is None or snapshot.html_path is None:
            return []

        html = snapshot.html_path.read_text(encoding="utf-8")
        mentions = parse_unlinked_mentions(html, domain)

    (directory / "unlinked_mentions.json").write_text(json.dumps(mentions, indent=2), encoding="utf-8")
    await polite_delay()
    return mentions


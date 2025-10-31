"""Competitor audit scraper collecting HTML snapshots for analysis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence

import structlog
from bs4 import BeautifulSoup

from .base import Snapshot, browser_context, capture_page, ensure_storage_path, polite_delay, run_with_retries

logger = structlog.get_logger(__name__)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def scrape_competitor_site(
    *,
    domain: str,
    paths: Sequence[str],
    storage_dir: Path,
) -> List[Dict[str, str]]:
    """Fetch competitor pages and record diffs when content changes."""

    snapshots: List[Dict[str, str]] = []
    base_dir = ensure_storage_path(storage_dir, "competitors", domain)
    history_file = base_dir / "history.json"
    history: Dict[str, str]
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text())
        except json.JSONDecodeError:
            logger.warning('scraper.competitor.history_corrupt', file=str(history_file))
            history = {}
    else:
        history = {}

    async with browser_context() as context:
        for path in paths:
            url = f"https://{domain}{path}"
            page_dir = ensure_storage_path(base_dir, path.strip("/") or "root")
            logger.info("scraper.competitor.fetch", url=url)

            async def _fetch() -> Snapshot:
                return await capture_page(
                    context,
                    url,
                    storage_dir=page_dir,
                    screenshot=True,
                )

            snapshot = await run_with_retries(_fetch)
            if snapshot is None or snapshot.html_path is None:
                continue

            html = snapshot.html_path.read_text(encoding="utf-8")
            digest = compute_hash(html)
            previous_digest = history.get(url)
            changed = digest != previous_digest

            if changed:
                soup = BeautifulSoup(html, "lxml")
                text_excerpt = " ".join(soup.stripped_strings)[:5000]
                snapshots.append(
                    {
                        "url": url,
                        "hash": digest,
                        "changed": True,
                        "html_path": str(snapshot.html_path),
                        "screenshot_path": str(snapshot.screenshot_path) if snapshot.screenshot_path else None,
                        "text_excerpt": text_excerpt,
                    }
                )
                history[url] = digest
                logger.info("scraper.competitor.changed", url=url)
            else:
                logger.debug("scraper.competitor.unchanged", url=url)

            await polite_delay()

    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return snapshots


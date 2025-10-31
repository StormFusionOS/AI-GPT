"""Citations scraper: discover NAP listings across directory sites."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

import structlog
from bs4 import BeautifulSoup

from .base import Snapshot, browser_context, capture_page, ensure_storage_path, polite_delay, run_with_retries

logger = structlog.get_logger(__name__)

CITATION_SITES = {
    "yelp": "https://www.yelp.com/search?find_desc={query}",
    "yellowpages": "https://www.yellowpages.com/search?search_terms={query}",
}


def parse_citation_html(html: str) -> List[Dict[str, Any]]:
    """Extract citation details from HTML snippets."""

    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, Any]] = []
    listings = soup.select(".businessName a, a.business-name")
    for listing in listings[:10]:
        parent = listing.find_parent("div")
        name = listing.get_text(strip=True)
        address = parent.select_one(".street-address, .businessLocation")
        phone = parent.select_one(".phones, .business-phone")
        results.append(
            {
                "name": name,
                "link": listing.get("href"),
                "address": address.get_text(strip=True) if address else None,
                "phone": phone.get_text(strip=True) if phone else None,
            }
        )
    return results


async def scrape_citations(
    *,
    business_name: str,
    location: str,
    storage_dir: Path,
    custom_sources: Sequence[str] | None = None,
) -> List[Dict[str, Any]]:
    """Scrape supported citation directories for mentions of the business."""

    sources = CITATION_SITES.copy()
    if custom_sources:
        sources.update({f"custom_{i}": url for i, url in enumerate(custom_sources)})

    results: List[Dict[str, Any]] = []
    query = f"{business_name} {location}".replace(" ", "+")

    async with browser_context() as context:
        for key, template in sources.items():
            url = template.format(query=query)
            logger.info("scraper.citations.fetch", source=key, url=url)

            async def _fetch() -> Snapshot:
                directory = ensure_storage_path(storage_dir, "citations", key)
                return await capture_page(
                    context,
                    url,
                    storage_dir=directory,
                    screenshot=False,
                )

            snapshot = await run_with_retries(_fetch)
            if snapshot is None or snapshot.html_path is None:
                continue

            html = snapshot.html_path.read_text(encoding="utf-8")
            parsed = parse_citation_html(html)
            results.extend(parsed)
            await polite_delay()

    (storage_dir / "citations_summary.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    return results


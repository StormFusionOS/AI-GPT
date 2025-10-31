"""SERP scraper collecting organic rankings and people-also-ask data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

import structlog
from bs4 import BeautifulSoup

from .base import Snapshot, browser_context, capture_page, ensure_storage_path, polite_delay, run_with_retries

logger = structlog.get_logger(__name__)

GOOGLE_SERP_URL = "https://www.google.com/search?q={query}&num={num}&hl={lang}"


def parse_serp(html: str) -> Dict[str, List[Dict[str, str]]]:
    """Parse organic results and people-also-ask questions."""

    soup = BeautifulSoup(html, "lxml")
    organic: List[Dict[str, str]] = []
    for rank, result in enumerate(soup.select("div.g"), start=1):
        link = result.select_one("a")
        title = result.select_one("h3")
        snippet = result.select_one("div.VwiC3b")
        if not link or not title:
            continue
        organic.append(
            {
                "rank": str(rank),
                "url": link.get("href"),
                "title": title.get_text(strip=True),
                "snippet": snippet.get_text(strip=True) if snippet else "",
            }
        )

    paa: List[Dict[str, str]] = []
    for idx, question in enumerate(soup.select("div[jsname='Cpkphb']"), start=1):
        q_text = question.get_text(" ", strip=True)
        if q_text:
            paa.append({"position": str(idx), "question": q_text})

    return {"organic": organic, "people_also_ask": paa}


async def scrape_serp(
    *,
    query: str,
    storage_dir: Path,
    num_results: int = 10,
    lang: str = "en",
) -> Dict[str, List[Dict[str, str]]]:
    """Scrape Google SERP for a query and persist the parsed payload."""

    serp_dir = ensure_storage_path(storage_dir, "serp", query.replace(" ", "_"))

    async with browser_context() as context:
        async def _fetch() -> Snapshot:
            return await capture_page(
                context,
                GOOGLE_SERP_URL.format(query=query.replace(" ", "+"), num=num_results, lang=lang),
                storage_dir=serp_dir,
                screenshot=True,
            )

        snapshot = await run_with_retries(_fetch)
        if snapshot is None or snapshot.html_path is None:
            return {"organic": [], "people_also_ask": []}

        html = snapshot.html_path.read_text(encoding="utf-8")
        payload = parse_serp(html)

    (serp_dir / "serp.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    await polite_delay()
    return payload


async def scrape_keywords(keywords: Sequence[str], storage_dir: Path) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """Scrape multiple keywords sequentially."""

    results: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    for keyword in keywords:
        logger.info("scraper.serp.keyword", keyword=keyword)
        results[keyword] = await scrape_serp(query=keyword, storage_dir=storage_dir)
    return results


"""Run the entire scraping stack sequentially."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Sequence

import structlog

from . import backlinks, citations, competitors, serp, unlinked_mentions

logger = structlog.get_logger(__name__)


async def run_all_scrapers(
    *,
    business_name: str,
    domain: str,
    competitor_domains: Sequence[str],
    keyword_list: Sequence[str],
    storage_dir: Path,
) -> None:
    """Execute all scraper workflows and log their completion."""

    storage_dir.mkdir(parents=True, exist_ok=True)

    await citations.scrape_citations(
        business_name=business_name,
        location="",
        storage_dir=storage_dir,
        custom_sources=None,
    )

    await backlinks.scrape_backlinks(domain=domain, storage_dir=storage_dir)

    competitor_tasks = [
        competitors.scrape_competitor_site(
            domain=comp,
            paths=("/", "/services", "/blog"),
            storage_dir=storage_dir,
        )
        for comp in competitor_domains
    ]
    await asyncio.gather(*competitor_tasks)

    await serp.scrape_keywords(keyword_list, storage_dir)
    await unlinked_mentions.scrape_unlinked_mentions(
        brand=business_name,
        domain=domain,
        storage_dir=storage_dir,
    )

    logger.info("scraper.run_all.complete")


def main() -> None:
    asyncio.run(
        run_all_scrapers(
            business_name="Example Co",
            domain="example.com",
            competitor_domains=["competitor1.com", "competitor2.com"],
            keyword_list=["best plumber", "emergency plumber"],
            storage_dir=Path("data/snapshots"),
        )
    )


if __name__ == "__main__":
    main()


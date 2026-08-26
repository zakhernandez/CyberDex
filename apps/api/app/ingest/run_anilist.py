"""CLI entry point for AniList anime ingestion.

Usage:
    uv run python -m app.ingest.run_anilist
"""

import asyncio
import logging
from collections import Counter

from app.database import SessionLocal
from app.ingest.anilist_client import AnilistClient
from app.ingest.anilist_ingestor import ingest_anime
from app.ingest.anilist_mapper import map_anilist_media


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# AniList tags to ingest. Case-sensitive; must match AniList's tag names exactly.
TAGS = [
    "Cyberpunk",
    "Dystopia",
    "Post-Apocalyptic",
    "Artificial Intelligence",
    "Virtual World",
]

MAX_PAGES_PER_TAG = 5  # 50 per page = up to 250 per tag


async def ingest_tag(client: AnilistClient, tag: str) -> None:
    logger.info(f"Fetching AniList tag: {tag}")
    actions: Counter[str] = Counter()

    for page in range(1, MAX_PAGES_PER_TAG + 1):
        try:
            result = await client.search_by_tag(tag, page=page, per_page=50)
        except Exception as e:
            logger.exception(f"Failed fetching page {page} for tag {tag}: {e}")
            break

        page_data = result.get("Page", {})
        media_list = page_data.get("media", [])
        page_info = page_data.get("pageInfo", {})

        logger.info(
            f"  Page {page}: {len(media_list)} entries (total for tag: {page_info.get('total')})"
        )

        for media in media_list:
            mapped = map_anilist_media(media)
            if mapped is None:
                actions["skipped_no_title"] += 1
                continue

            with SessionLocal() as db:
                result = ingest_anime(db, mapped)
                actions[result.action] += 1
                if result.action == "created":
                    logger.info(f"    + {result.title} ({mapped.year})")
                elif result.action == "error":
                    logger.error(f"    ! {result.title}: {result.error}")

        # Stop if no more pages
        if not page_info.get("hasNextPage"):
            break

    logger.info(f"Tag '{tag}' done: {dict(actions)}")


async def main() -> None:
    async with AnilistClient() as client:
        for tag in TAGS:
            await ingest_tag(client, tag)
            logger.info("─" * 60)


if __name__ == "__main__":
    asyncio.run(main())
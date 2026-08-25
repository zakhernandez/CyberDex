"""CLI entry point for TMDB ingestion.

Usage:
    uv run python -m app.ingest.run_tmdb
"""

import asyncio
import logging
from collections import Counter

from app.database import SessionLocal
from app.ingest.tmdb_client import TmdbClient
from app.ingest.tmdb_ingestor import ingest_film
from app.ingest.tmdb_mapper import map_tmdb_movie


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Keywords to ingest. Add more here later to expand the catalog.
KEYWORDS = [
    "cyberpunk",
    "dystopia",
    "artificial intelligence",
    "hacker",
    "virtual reality",
]


async def ingest_by_keyword(client: TmdbClient, keyword_name: str) -> None:
    logger.info(f"Looking up keyword: {keyword_name}")
    keyword_id = await client.find_keyword_id(keyword_name)
    if keyword_id is None:
        logger.warning(f"Keyword not found: {keyword_name}")
        return

    logger.info(f"Discovering movies for keyword '{keyword_name}' (id={keyword_id})")
    actions: Counter[str] = Counter()

    # Iterate pages
    page = 1
    total_pages = 1  # updated after first request
    while page <= total_pages:
        listing = await client.discover_movies_by_keyword(keyword_id, page=page)
        total_pages = min(listing.get("total_pages", 1), 20)  # cap at 20 pages
        movies = listing.get("results", [])
        logger.info(
            f"  Page {page}/{total_pages}: {len(movies)} movies to process"
        )

        for movie in movies:
            tmdb_id = movie["id"]
            # Fetch full details (with credits)
            details = await client.get_movie_details(tmdb_id)
            mapped = map_tmdb_movie(details)

            with SessionLocal() as db:
                result = ingest_film(db, mapped)
                actions[result.action] += 1
                if result.action == "created":
                    logger.info(f"    + {result.title} ({mapped.year})")
                elif result.action == "error":
                    logger.error(f"    ! {result.title}: {result.error}")

        page += 1

    logger.info(
        f"Keyword '{keyword_name}' done: "
        f"{dict(actions)}"
    )


async def main() -> None:
    async with TmdbClient() as client:
        for keyword in KEYWORDS:
            await ingest_by_keyword(client, keyword)
            logger.info("─" * 60)


if __name__ == "__main__":
    asyncio.run(main())
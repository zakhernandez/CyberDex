"""CLI entry point for OpenLibrary book ingestion.

Usage:
    uv run python -m app.ingest.run_openlibrary
"""

import asyncio
import logging
from collections import Counter

from app.database import SessionLocal
from app.ingest.openlibrary_client import OpenLibraryClient
from app.ingest.openlibrary_ingestor import ingest_book
from app.ingest.openlibrary_mapper import map_openlibrary_work


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Subjects to ingest. OpenLibrary uses underscore-separated lowercase subjects.
SUBJECTS = [
    "cyberpunk_fiction",
    "cyberpunk",
    "dystopian_fiction",
    "artificial_intelligence_fiction",
    "virtual_reality_fiction",
]

MAX_WORKS_PER_SUBJECT = 200  # cap so we don't chase every dystopian novel ever


async def _fetch_authors(
    client: OpenLibraryClient, author_refs: list[dict]
) -> list[dict]:
    """Given author references from a work, fetch their full records."""
    authors: list[dict] = []
    for ref in author_refs:
        # References look like {"author": {"key": "/authors/OL5202823A"}, "type": ...}
        author_ref = ref.get("author", {})
        key = author_ref.get("key")
        if not key:
            continue
        try:
            data = await client.get_author(key)
            authors.append(data)
        except Exception as e:
            logger.warning(f"Failed to fetch author {key}: {e}")
    return authors


async def ingest_subject(client: OpenLibraryClient, subject: str) -> None:
    logger.info(f"Fetching subject: {subject}")
    actions: Counter[str] = Counter()

    fetched = 0
    offset = 0
    page_size = 50

    while fetched < MAX_WORKS_PER_SUBJECT:
        limit = min(page_size, MAX_WORKS_PER_SUBJECT - fetched)
        listing = await client.get_subject(subject, limit=limit, offset=offset)
        works = listing.get("works", [])
        if not works:
            break

        logger.info(
            f"  Offset {offset}: {len(works)} works to process"
        )

        for work_summary in works:
            work_key = work_summary.get("key")
            if not work_key:
                actions["error"] += 1
                continue

            try:
                # Fetch full work + authors + editions
                work_payload = await client.get_work(work_key)
                author_refs = work_payload.get("authors", [])
                author_payloads = await _fetch_authors(client, author_refs)

                # Get a few editions for cover/ISBN/pages
                try:
                    editions_payload = await client.get_editions_for_work(
                        work_key, limit=5
                    )
                except Exception:
                    editions_payload = None

                mapped = map_openlibrary_work(
                    work_payload, author_payloads, editions_payload
                )
                if mapped is None:
                    actions["skipped_no_title"] += 1
                    continue

                with SessionLocal() as db:
                    result = ingest_book(db, mapped)
                    actions[result.action] += 1
                    if result.action == "created":
                        logger.info(f"    + {result.title} ({mapped.year})")
                    elif result.action == "error":
                        logger.error(f"    ! {result.title}: {result.error}")

            except Exception as e:
                actions["error"] += 1
                logger.exception(f"Failed processing {work_key}: {e}")

        fetched += len(works)
        offset += len(works)
        # If we got fewer than we asked for, we hit the end
        if len(works) < limit:
            break

    logger.info(f"Subject '{subject}' done: {dict(actions)}")


async def main() -> None:
    async with OpenLibraryClient() as client:
        for subject in SUBJECTS:
            await ingest_subject(client, subject)
            logger.info("─" * 60)


if __name__ == "__main__":
    asyncio.run(main())
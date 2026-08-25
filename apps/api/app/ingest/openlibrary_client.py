"""Thin async client for OpenLibrary. No API key needed."""

import asyncio
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


class OpenLibraryClient:
    """
    Wraps the OpenLibrary REST API. Use as async context manager:

        async with OpenLibraryClient() as client:
            works = await client.get_subject("cyberpunk_fiction")
    """

    def __init__(self, requests_per_second: float = 5.0):
        self._base_url = settings.openlibrary_base_url
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_delay = 1.0 / requests_per_second

    async def __aenter__(self) -> "OpenLibraryClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={"User-Agent": "CyberDex/0.1 (learning project)"},
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        assert self._client is not None, "Use OpenLibraryClient as async context manager"
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        await asyncio.sleep(self._rate_limit_delay)
        return response.json()

    async def get_subject(
        self, subject: str, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        """Get works tagged with the given subject."""
        return await self._get(
            f"/subjects/{subject}.json",
            limit=limit,
            offset=offset,
        )

    async def get_work(self, work_key: str) -> dict[str, Any]:
        """Get details for a specific work. work_key is like 'OL27448W' or '/works/OL27448W'."""
        # Handle both formats — with and without the '/works/' prefix
        work_id = work_key.replace("/works/", "").strip("/")
        return await self._get(f"/works/{work_id}.json")

    async def get_author(self, author_key: str) -> dict[str, Any]:
        """Get details for an author. Key is like 'OL5202823A' or '/authors/OL5202823A'."""
        author_id = author_key.replace("/authors/", "").strip("/")
        return await self._get(f"/authors/{author_id}.json")

    async def get_editions_for_work(
        self, work_key: str, limit: int = 5
    ) -> dict[str, Any]:
        """Get editions for a work, for finding cover/ISBN/page count."""
        work_id = work_key.replace("/works/", "").strip("/")
        return await self._get(f"/works/{work_id}/editions.json", limit=limit)
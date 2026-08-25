"""Thin async client for TMDB. Knows nothing about the database."""

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


class TmdbClient:
    """
    Wraps TMDB's REST API with proper retries, timeouts, and rate limiting.

    Use as an async context manager to ensure the HTTP client is closed:

        async with TmdbClient() as client:
            movies = await client.discover_movies(keyword_id=12190)
    """

    def __init__(self, requests_per_second: float = 4.0):
        self._base_url = settings.tmdb_base_url
        self._api_key = settings.tmdb_api_key
        self._client: httpx.AsyncClient | None = None
        # TMDB allows ~40 req/10s = 4 rps. We stay under to be polite.
        self._rate_limit_delay = 1.0 / requests_per_second

    async def __aenter__(self) -> "TmdbClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            params={"api_key": self._api_key},
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
        assert self._client is not None, "Use TmdbClient as async context manager"
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        await asyncio.sleep(self._rate_limit_delay)
        return response.json()

    async def discover_movies_by_keyword(
        self, keyword_id: int, page: int = 1
    ) -> dict[str, Any]:
        """Get a page of movies tagged with the given keyword."""
        return await self._get(
            "/discover/movie",
            with_keywords=str(keyword_id),
            page=page,
            sort_by="popularity.desc",
        )

    async def get_movie_details(self, tmdb_id: int) -> dict[str, Any]:
        """Get full details for a specific movie, including credits and keywords."""
        return await self._get(
            f"/movie/{tmdb_id}",
            append_to_response="credits,keywords,external_ids",
        )

    async def find_keyword_id(self, name: str) -> int | None:
        """Look up a keyword's ID by name. Returns None if not found."""
        data = await self._get("/search/keyword", query=name)
        results = data.get("results", [])
        for result in results:
            if result["name"].lower() == name.lower():
                return int(result["id"])
        return None
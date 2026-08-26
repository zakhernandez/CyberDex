"""Thin async client for AniList's GraphQL API."""

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


# ─────────────────────────────────────────────────────────
# GraphQL query strings
# ─────────────────────────────────────────────────────────

# Page of media filtered by tag. Returns just what we need.
SEARCH_BY_TAG_QUERY = """
query ($tag: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      currentPage
      lastPage
      hasNextPage
      total
    }
    media(tag: $tag, type: ANIME, sort: POPULARITY_DESC) {
      id
      idMal
      title {
        english
        romaji
        native
      }
      startDate { year }
      episodes
      format
      source
      description(asHtml: false)
      coverImage { extraLarge large }
      studios(isMain: true) {
        nodes {
          id
          name
        }
      }
      countryOfOrigin
    }
  }
}
"""


# ─────────────────────────────────────────────────────────
# The client
# ─────────────────────────────────────────────────────────


class AnilistClient:
    """
    Wraps AniList's GraphQL API. Use as async context manager:

        async with AnilistClient() as client:
            page = await client.search_by_tag("Cyberpunk", page=1)
    """

    def __init__(self, requests_per_second: float = 1.5):
        # AniList limits: 90 requests/minute (1.5/second)
        self._url = settings.anilist_graphql_url
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_delay = 1.0 / requests_per_second

    async def __aenter__(self) -> "AnilistClient":
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _post_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        assert self._client is not None, "Use AnilistClient as async context manager"
        response = await self._client.post(
            self._url,
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise RuntimeError(f"AniList GraphQL errors: {data['errors']}")
        await asyncio.sleep(self._rate_limit_delay)
        return data["data"]

    async def search_by_tag(
        self, tag: str, page: int = 1, per_page: int = 50
    ) -> dict[str, Any]:
        """Get a page of anime matching a specific tag."""
        return await self._post_query(
            SEARCH_BY_TAG_QUERY,
            {"tag": tag, "page": page, "perPage": per_page},
        )
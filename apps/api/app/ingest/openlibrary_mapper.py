"""Maps OpenLibrary API payloads to our internal data structures."""

import re
from dataclasses import dataclass, field
from typing import Any

from app.config import settings


@dataclass
class MappedBookCreator:
    name: str
    role: str  # 'author'
    credit_order: int | None = None


@dataclass
class MappedBook:
    """A book in our schema's shape, ready to be inserted."""

    # Works fields
    title: str
    original_title: str | None
    original_language: str | None
    sort_title: str
    year: int | None
    synopsis: str | None
    cover_url: str | None
    slug: str

    # Book-specific fields
    page_count: int | None
    isbn_13: str | None

    # External IDs
    openlibrary_id: str  # e.g. "OL27448W"

    # Creators
    creators: list[MappedBookCreator] = field(default_factory=list)


# ─────────────────────────────────────────────────────────
# Helpers (same style as TMDB mapper)
# ─────────────────────────────────────────────────────────

_LEADING_ARTICLES = {
    "the", "a", "an",
    "le", "la", "les",
    "der", "das", "die",
    "el", "los", "las",
}


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _make_sort_title(title: str) -> str:
    words = title.split(maxsplit=1)
    if len(words) == 2 and words[0].lower() in _LEADING_ARTICLES:
        return words[1]
    return title


def _slug_with_year(slug: str, year: int | None) -> str:
    if year:
        return f"{slug}-{year}"
    return slug


def _extract_year_from_work(work_payload: dict[str, Any]) -> int | None:
    """Try to get the earliest publication year from various fields."""
    # first_publish_date might be '1984', 'June 1984', '1984-06-01', etc.
    raw = work_payload.get("first_publish_date")
    if raw:
        match = re.search(r"\d{4}", raw)
        if match:
            year = int(match.group())
            if 1400 < year < 2100:
                return year
    return None


def _extract_synopsis(work_payload: dict[str, Any]) -> str | None:
    """Descriptions might be strings or {'type': ..., 'value': ...} dicts."""
    desc = work_payload.get("description")
    if not desc:
        return None
    if isinstance(desc, str):
        return desc.strip() or None
    if isinstance(desc, dict):
        value = desc.get("value")
        return value.strip() if value else None
    return None


def _cover_url_from_id(cover_id: int | None) -> str | None:
    """OpenLibrary covers are served from a separate CDN, referenced by ID."""
    if not cover_id:
        return None
    return f"{settings.openlibrary_covers_base}/id/{cover_id}-L.jpg"


def _extract_cover_from_work(work_payload: dict[str, Any]) -> str | None:
    """Work has a 'covers' list; take the first."""
    covers = work_payload.get("covers", [])
    if covers:
        return _cover_url_from_id(covers[0])
    return None


def _pick_edition_data(
    editions_payload: dict[str, Any],
) -> tuple[int | None, str | None, str | None]:
    """
    From an editions payload, find the best edition to pull metadata from.
    Returns (page_count, isbn_13, cover_url).
    """
    entries = editions_payload.get("entries", [])

    page_count: int | None = None
    isbn_13: str | None = None
    cover_url: str | None = None

    for edition in entries:
        # First edition with a page count wins
        if page_count is None and edition.get("number_of_pages"):
            page_count = int(edition["number_of_pages"])

        # First ISBN-13 wins
        if isbn_13 is None:
            isbns = edition.get("isbn_13", [])
            if isbns:
                isbn_13 = isbns[0]

        # First cover wins
        if cover_url is None:
            covers = edition.get("covers", [])
            if covers:
                cover_url = _cover_url_from_id(covers[0])

        # Short-circuit once we have all three
        if page_count and isbn_13 and cover_url:
            break

    return page_count, isbn_13, cover_url


# ─────────────────────────────────────────────────────────
# The mapper
# ─────────────────────────────────────────────────────────


def map_openlibrary_work(
    work_payload: dict[str, Any],
    author_payloads: list[dict[str, Any]],
    editions_payload: dict[str, Any] | None = None,
) -> MappedBook | None:
    """
    Turn an OpenLibrary work (plus its authors and editions) into our schema.

    Returns None if the work is missing essential data (no title).
    """
    title = work_payload.get("title")
    if not title:
        return None  # Skip untitled works

    title = title.strip()
    year = _extract_year_from_work(work_payload)
    base_slug = _slugify(title)
    slug = _slug_with_year(base_slug, year)

    synopsis = _extract_synopsis(work_payload)

    # Cover — prefer work-level, fall back to editions
    cover_url = _extract_cover_from_work(work_payload)

    # Pull page count, ISBN, and (fallback) cover from editions
    page_count: int | None = None
    isbn_13: str | None = None
    if editions_payload:
        e_pages, e_isbn, e_cover = _pick_edition_data(editions_payload)
        page_count = e_pages
        isbn_13 = e_isbn
        if not cover_url:
            cover_url = e_cover

    # Openlibrary work key looks like '/works/OL27448W'
    key = work_payload.get("key", "")
    openlibrary_id = key.replace("/works/", "").strip("/")

    creators = [
        MappedBookCreator(
            name=author.get("name", "").strip() or "Unknown",
            role="author",
            credit_order=i,
        )
        for i, author in enumerate(author_payloads)
        if author.get("name")
    ]

    return MappedBook(
        title=title,
        original_title=None,  # OpenLibrary rarely provides translation info
        original_language=None,
        sort_title=_make_sort_title(title),
        year=year,
        synopsis=synopsis,
        cover_url=cover_url,
        slug=slug,
        page_count=page_count,
        isbn_13=isbn_13,
        openlibrary_id=openlibrary_id,
        creators=creators,
    )
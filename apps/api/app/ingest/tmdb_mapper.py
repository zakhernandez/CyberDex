"""Maps TMDB API payloads to the internal data structures.

Pure functions: no I/O, no database, no side effects. Testable in isolation.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.config import settings


@dataclass
class MappedCreator:
    name: str
    role: str            # 'director', 'screenwriter', 'studio', etc.
    credit_order: int | None = None


@dataclass
class MappedFilm:
    """A film in the schema's shape, ready to be inserted."""

    # Works fields
    title: str
    original_title: str | None
    original_language: str | None
    sort_title: str
    year: int | None
    synopsis: str | None
    cover_url: str | None
    slug: str

    # Film-specific fields
    runtime_minutes: int | None
    tagline: str | None

    # External IDs
    tmdb_id: int
    imdb_id: str | None

    # Creators
    creators: list[MappedCreator] = field(default_factory=list)


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

_LEADING_ARTICLES = {
    "the", "a", "an",
    "le", "la", "les",
    "der", "das", "die",
    "el", "los", "las",
}


def _slugify(text: str) -> str:
    """Turn a title into a URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _make_sort_title(title: str) -> str:
    """Strip leading article for sorting. 'The Matrix' -> 'Matrix'."""
    words = title.split(maxsplit=1)
    if len(words) == 2 and words[0].lower() in _LEADING_ARTICLES:
        return words[1]
    return title


def _extract_year(release_date: str | None) -> int | None:
    """TMDB gives us '1982-06-25'; we want 1982. Handles missing/malformed."""
    if not release_date:
        return None
    try:
        return int(release_date.split("-")[0])
    except (ValueError, IndexError):
        return None


def _make_cover_url(poster_path: str | None) -> str | None:
    """Construct full image URL from TMDB's path."""
    if not poster_path:
        return None
    return f"{settings.tmdb_image_base}{poster_path}"


def _slug_with_year(slug: str, year: int | None) -> str:
    """Append year to slug for disambiguation. Prevents collisions
    like the-thing (1982 vs 2011)."""
    if year:
        return f"{slug}-{year}"
    return slug


# ─────────────────────────────────────────────────────────
# The mapper
# ─────────────────────────────────────────────────────────


def map_tmdb_movie(payload: dict[str, Any]) -> MappedFilm:
    """Turn a full TMDB /movie/{id} response into our schema shape."""

    title = payload["title"]  # TMDB always provides a display title
    original_title = payload.get("original_title")
    if original_title == title:
        original_title = None  # Don't store if identical

    year = _extract_year(payload.get("release_date"))
    base_slug = _slugify(title)
    slug = _slug_with_year(base_slug, year)

    # Extract creators from credits
    creators: list[MappedCreator] = []
    credits = payload.get("credits", {})

    # Directors from crew (job == 'Director')
    for i, member in enumerate(credits.get("crew", [])):
        if member.get("job") == "Director":
            creators.append(MappedCreator(
                name=member["name"],
                role="director",
                credit_order=i,
            ))

    # Screenwriters from crew (department == 'Writing')
    for i, member in enumerate(credits.get("crew", [])):
        if member.get("department") == "Writing":
            creators.append(MappedCreator(
                name=member["name"],
                role="screenwriter",
                credit_order=i,
            ))

    # Production companies as studios
    for i, company in enumerate(payload.get("production_companies", [])):
        creators.append(MappedCreator(
            name=company["name"],
            role="studio",
            credit_order=i,
        ))

    return MappedFilm(
        title=title,
        original_title=original_title,
        original_language=payload.get("original_language"),
        sort_title=_make_sort_title(title),
        year=year,
        synopsis=payload.get("overview") or None,
        cover_url=_make_cover_url(payload.get("poster_path")),
        slug=slug,
        runtime_minutes=payload.get("runtime"),
        tagline=payload.get("tagline") or None,
        tmdb_id=payload["id"],
        imdb_id=payload.get("external_ids", {}).get("imdb_id"),
        creators=creators,
    )
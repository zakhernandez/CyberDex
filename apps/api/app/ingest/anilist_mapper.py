"""Maps AniList GraphQL responses to our internal data structures."""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MappedAnimeCreator:
    name: str
    role: str  # 'studio'
    credit_order: int | None = None


@dataclass
class MappedAnime:
    """An anime in our schema's shape, ready to be inserted."""

    # Works fields
    title: str
    original_title: str | None
    original_language: str | None
    sort_title: str
    year: int | None
    synopsis: str | None
    cover_url: str | None
    slug: str

    # Anime-specific fields
    episodes: int | None
    format: str | None  # our AnimeFormat enum value (lowercase)
    source: str | None  # our AnimeSource enum value

    # External IDs
    anilist_id: int
    mal_id: int | None

    # Creators
    creators: list[MappedAnimeCreator] = field(default_factory=list)


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


def _strip_html(text: str | None) -> str | None:
    """AniList descriptions may contain <br>, <i>, etc. Strip them."""
    if not text:
        return None
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    return text or None


# ─────────────────────────────────────────────────────────
# Enum mappings (AniList's raw values → our enum values)
# ─────────────────────────────────────────────────────────

_FORMAT_MAP = {
    "TV": "TV",
    "TV_SHORT": "TV_SHORT",
    "MOVIE": "FILM",  # note: AniList's MOVIE → our FILM
    "SPECIAL": "SPECIAL",
    "OVA": "OVA",
    "ONA": "ONA",
    "MUSIC": "MUSIC",
}

_SOURCE_MAP = {
    "MANGA": "MANGA",
    "LIGHT_NOVEL": "LIGHT_NOVEL",
    "ORIGINAL": "ORIGINAL",
    "NOVEL": "NOVEL",
    "VIDEO_GAME": "VIDEO_GAME",
    "VISUAL_NOVEL": "OTHER",   # we don't distinguish
    "DOUJINSHI": "OTHER",
    "ANIME": "OTHER",
    "WEB_NOVEL": "NOVEL",
    "LIVE_ACTION": "OTHER",
    "GAME": "VIDEO_GAME",
    "COMIC": "OTHER",
    "MULTIMEDIA_PROJECT": "OTHER",
    "PICTURE_BOOK": "OTHER",
    "OTHER": "OTHER",
}


# ─────────────────────────────────────────────────────────
# The mapper
# ─────────────────────────────────────────────────────────


def map_anilist_media(payload: dict[str, Any]) -> MappedAnime | None:
    """Turn an AniList media entry into our schema shape.

    Returns None if the entry is missing essential data.
    """
    titles = payload.get("title") or {}
    english = titles.get("english")
    romaji = titles.get("romaji")
    native = titles.get("native")

    # Prefer English; fall back to romaji; last resort native
    title = english or romaji or native
    if not title:
        return None

    title = title.strip()

    # Original title is the native (Japanese) if we're not already using it
    original_title = native if native and native != title else None

    year = None
    start_date = payload.get("startDate") or {}
    if start_date.get("year"):
        year = int(start_date["year"])

    base_slug = _slugify(title)
    slug = _slug_with_year(base_slug, year)

    # Cover: prefer extraLarge
    cover = None
    cover_image = payload.get("coverImage") or {}
    if cover_image.get("extraLarge"):
        cover = cover_image["extraLarge"]
    elif cover_image.get("large"):
        cover = cover_image["large"]

    # Format and source: map to our enum values, keep None if unmapped
    raw_format = payload.get("format")
    fmt = _FORMAT_MAP.get(raw_format) if raw_format else None

    raw_source = payload.get("source")
    source = _SOURCE_MAP.get(raw_source, "OTHER") if raw_source else None

    # Studios as creators
    creators: list[MappedAnimeCreator] = []
    studios_data = payload.get("studios") or {}
    for i, studio_node in enumerate(studios_data.get("nodes", [])):
        studio_name = studio_node.get("name")
        if studio_name:
            creators.append(MappedAnimeCreator(
                name=studio_name.strip(),
                role="studio",
                credit_order=i,
            ))

    # Language: anime is usually Japanese but AniList gives us countryOfOrigin
    country = payload.get("countryOfOrigin")
    lang_map = {"JP": "ja", "KR": "ko", "CN": "zh", "TW": "zh"}
    original_language = lang_map.get(country)

    return MappedAnime(
        title=title,
        original_title=original_title,
        original_language=original_language,
        sort_title=_make_sort_title(title),
        year=year,
        synopsis=_strip_html(payload.get("description")),
        cover_url=cover,
        slug=slug,
        episodes=payload.get("episodes"),
        format=fmt,
        source=source,
        anilist_id=int(payload["id"]),
        mal_id=int(payload["idMal"]) if payload.get("idMal") else None,
        creators=creators,
    )
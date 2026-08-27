"""Pydantic schemas for API request/response bodies."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    AnimeFormat,
    AnimeSource,
    CreatorKind,
    CreatorRole,
    ExternalSource,
    RelationshipType,
    WorkKind,
)


# ─────────────────────────────────────────────────────────
# Creators
# ─────────────────────────────────────────────────────────


class CreatorRead(BaseModel):
    id: int
    name: str
    kind: CreatorKind
    slug: str

    model_config = ConfigDict(from_attributes=True)


class WorkCreatorRead(BaseModel):
    """Creator with their role on a specific work."""

    creator: CreatorRead
    role: CreatorRole
    credit_order: int | None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────
# External IDs
# ─────────────────────────────────────────────────────────


class ExternalIdRead(BaseModel):
    source: ExternalSource
    external_id: str
    url: str | None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────
# Works (list + detail)
# ─────────────────────────────────────────────────────────


class WorkListItem(BaseModel):
    """A work in a list — minimal fields for browsing."""

    id: int
    kind: WorkKind
    title: str
    year: int | None
    cover_url: str | None
    slug: str

    model_config = ConfigDict(from_attributes=True)


class FilmDetail(BaseModel):
    runtime_minutes: int | None
    tagline: str | None

    model_config = ConfigDict(from_attributes=True)


class BookDetail(BaseModel):
    page_count: int | None
    isbn_13: str | None

    model_config = ConfigDict(from_attributes=True)


class AnimeDetail(BaseModel):
    episodes: int | None
    format: AnimeFormat | None
    source: AnimeSource | None

    model_config = ConfigDict(from_attributes=True)


class WorkDetail(BaseModel):
    """A single work with everything about it."""

    id: int
    kind: WorkKind
    title: str
    original_title: str | None
    original_language: str | None
    year: int | None
    synopsis: str | None
    cover_url: str | None
    slug: str

    film: FilmDetail | None = None
    book: BookDetail | None = None
    anime: AnimeDetail | None = None

    creators: list[WorkCreatorRead] = []
    external_ids: list[ExternalIdRead] = []

    model_config = ConfigDict(from_attributes=True)


class WorkListResponse(BaseModel):
    """Paginated list of works."""

    items: list[WorkListItem]
    total: int
    page: int
    per_page: int
    has_next: bool


# ─────────────────────────────────────────────────────────
# Ratings
# ─────────────────────────────────────────────────────────


class RatingCreate(BaseModel):
    """Create or update a rating."""

    work_id: int
    score: int = Field(ge=1, le=10)


class RatingRead(BaseModel):
    id: int
    work_id: int
    score: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingWithWork(BaseModel):
    """A rating alongside minimal work info — for the ratings history view."""

    id: int
    score: int
    created_at: datetime
    updated_at: datetime
    work: WorkListItem

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────


class KindCount(BaseModel):
    kind: WorkKind
    count: int


class CatalogStats(BaseModel):
    total_works: int
    total_creators: int
    total_ratings: int
    by_kind: list[KindCount]


# ─────────────────────────────────────────────────────────
# Placeholder for relationships (schema only for now)
# ─────────────────────────────────────────────────────────


class WorkRelationshipRead(BaseModel):
    id: int
    to_work: WorkListItem
    relationship_type: RelationshipType
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
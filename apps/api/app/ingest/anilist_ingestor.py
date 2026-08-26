"""Ingests mapped AniList data into the database, idempotently."""

import logging
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.anilist_mapper import MappedAnime
from app.models import (
    Anime,
    AnimeFormat,
    AnimeSource,
    Creator,
    CreatorKind,
    CreatorRole,
    ExternalId,
    ExternalSource,
    Work,
    WorkCreator,
    WorkKind,
)


logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    anilist_id: int
    title: str
    action: str  # 'created' | 'skipped_existing' | 'error'
    work_id: int | None = None
    error: str | None = None


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _find_or_create_studio(db: Session, name: str) -> Creator:
    """Look up a studio by slug; create if not found."""
    slug = _slugify(name)
    stmt = select(Creator).where(Creator.slug == slug)
    existing = db.scalars(stmt).first()
    if existing:
        return existing
    creator = Creator(name=name, kind=CreatorKind.STUDIO, slug=slug)
    db.add(creator)
    db.flush()
    return creator


def _work_exists_for_anilist(db: Session, anilist_id: int) -> Work | None:
    """Check if we've already ingested this AniList entry."""
    stmt = (
        select(Work)
        .join(ExternalId, ExternalId.work_id == Work.id)
        .where(
            ExternalId.source == ExternalSource.ANILIST,
            ExternalId.external_id == str(anilist_id),
        )
    )
    return db.scalars(stmt).first()


def _resolve_slug_collision(db: Session, base_slug: str) -> str:
    slug = base_slug
    suffix = 1
    while True:
        stmt = select(Work).where(Work.slug == slug)
        if db.scalars(stmt).first() is None:
            return slug
        suffix += 1
        slug = f"{base_slug}-alt{suffix - 1}"


def ingest_anime(db: Session, mapped: MappedAnime) -> IngestResult:
    """Insert one mapped anime into the database. Idempotent by AniList ID."""

    existing = _work_exists_for_anilist(db, mapped.anilist_id)
    if existing:
        return IngestResult(
            anilist_id=mapped.anilist_id,
            title=mapped.title,
            action="skipped_existing",
            work_id=existing.id,
        )

    try:
        slug = _resolve_slug_collision(db, mapped.slug)

        work = Work(
            kind=WorkKind.ANIME,
            title=mapped.title,
            original_title=mapped.original_title,
            original_language=mapped.original_language,
            sort_title=mapped.sort_title,
            year=mapped.year,
            synopsis=mapped.synopsis,
            cover_url=mapped.cover_url,
            slug=slug,
        )
        db.add(work)
        db.flush()

        # Convert string enum values from mapper to actual enum members
        fmt_enum = AnimeFormat[mapped.format] if mapped.format else None
        source_enum = AnimeSource[mapped.source] if mapped.source else None

        anime = Anime(
            work_id=work.id,
            episodes=mapped.episodes,
            format=fmt_enum,
            source=source_enum,
        )
        db.add(anime)

        # External IDs
        db.add(ExternalId(
            work_id=work.id,
            source=ExternalSource.ANILIST,
            external_id=str(mapped.anilist_id),
            url=f"https://anilist.co/anime/{mapped.anilist_id}",
        ))
        if mapped.mal_id:
            db.add(ExternalId(
                work_id=work.id,
                source=ExternalSource.MAL,
                external_id=str(mapped.mal_id),
                url=f"https://myanimelist.net/anime/{mapped.mal_id}",
            ))

        # Studios as creators
        for mapped_creator in mapped.creators:
            creator = _find_or_create_studio(db, mapped_creator.name)
            existing_wc = db.get(
                WorkCreator, (work.id, creator.id, CreatorRole.STUDIO)
            )
            if existing_wc is None:
                db.add(WorkCreator(
                    work_id=work.id,
                    creator_id=creator.id,
                    role=CreatorRole.STUDIO,
                    credit_order=mapped_creator.credit_order,
                ))

        db.commit()
        return IngestResult(
            anilist_id=mapped.anilist_id,
            title=mapped.title,
            action="created",
            work_id=work.id,
        )

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to ingest {mapped.title}")
        return IngestResult(
            anilist_id=mapped.anilist_id,
            title=mapped.title,
            action="error",
            error=str(e),
        )
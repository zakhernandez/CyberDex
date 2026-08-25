"""Ingests mapped TMDB data into the database, idempotently."""

import logging
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.tmdb_mapper import MappedCreator, MappedFilm
from app.models import (
    Creator,
    CreatorKind,
    CreatorRole,
    ExternalId,
    ExternalSource,
    Film,
    Work,
    WorkCreator,
    WorkKind,
)


logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """What happened when tried to ingest one film."""

    tmdb_id: int
    title: str
    action: str      # 'created' | 'skipped_existing' | 'error'
    work_id: int | None = None
    error: str | None = None


def _slugify(text: str) -> str:
    """Same slugify as in mapper; duplicated here to keep ingestor self-contained."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _find_or_create_creator(
    db: Session, name: str, kind: CreatorKind
) -> Creator:
    """Look up a creator by slug; create if not found."""
    slug = _slugify(name)
    stmt = select(Creator).where(Creator.slug == slug)
    existing = db.scalars(stmt).first()
    if existing:
        return existing
    creator = Creator(name=name, kind=kind, slug=slug)
    db.add(creator)
    db.flush()  # get the ID without committing
    return creator


def _work_exists_for_tmdb(db: Session, tmdb_id: int) -> Work | None:
    """Check if we've already ingested this TMDB film."""
    stmt = (
        select(Work)
        .join(ExternalId, ExternalId.work_id == Work.id)
        .where(
            ExternalId.source == ExternalSource.TMDB,
            ExternalId.external_id == str(tmdb_id),
        )
    )
    return db.scalars(stmt).first()


_ROLE_TO_CREATOR_KIND = {
    "director": CreatorKind.PERSON,
    "screenwriter": CreatorKind.PERSON,
    "studio": CreatorKind.STUDIO,
}

_ROLE_TO_ENUM = {
    "director": CreatorRole.DIRECTOR,
    "screenwriter": CreatorRole.SCREENWRITER,
    "studio": CreatorRole.STUDIO,
}


def ingest_film(db: Session, mapped: MappedFilm) -> IngestResult:
    """Insert one mapped film into the database. Idempotent by TMDB ID."""

    existing = _work_exists_for_tmdb(db, mapped.tmdb_id)
    if existing:
        logger.debug(f"Skipping existing: {mapped.title} (tmdb {mapped.tmdb_id})")
        return IngestResult(
            tmdb_id=mapped.tmdb_id,
            title=mapped.title,
            action="skipped_existing",
            work_id=existing.id,
        )

    try:
        # Create the base work
        work = Work(
            kind=WorkKind.FILM,
            title=mapped.title,
            original_title=mapped.original_title,
            original_language=mapped.original_language,
            sort_title=mapped.sort_title,
            year=mapped.year,
            synopsis=mapped.synopsis,
            cover_url=mapped.cover_url,
            slug=mapped.slug,
        )
        db.add(work)
        db.flush()

        # Create the film-specific record
        film = Film(
            work_id=work.id,
            runtime_minutes=mapped.runtime_minutes,
            tagline=mapped.tagline,
        )
        db.add(film)

        # External IDs
        db.add(ExternalId(
            work_id=work.id,
            source=ExternalSource.TMDB,
            external_id=str(mapped.tmdb_id),
            url=f"https://www.themoviedb.org/movie/{mapped.tmdb_id}",
        ))
        if mapped.imdb_id:
            db.add(ExternalId(
                work_id=work.id,
                source=ExternalSource.IMDB,
                external_id=mapped.imdb_id,
                url=f"https://www.imdb.com/title/{mapped.imdb_id}/",
            ))

        # Creators
        for mapped_creator in mapped.creators:
            kind = _ROLE_TO_CREATOR_KIND[mapped_creator.role]
            role = _ROLE_TO_ENUM[mapped_creator.role]
            creator = _find_or_create_creator(db, mapped_creator.name, kind)
            # Avoid inserting duplicate (work, creator, role) tuples
            existing_wc = db.get(WorkCreator, (work.id, creator.id, role))
            if existing_wc is None:
                db.add(WorkCreator(
                    work_id=work.id,
                    creator_id=creator.id,
                    role=role,
                    credit_order=mapped_creator.credit_order,
                ))

        db.commit()
        return IngestResult(
            tmdb_id=mapped.tmdb_id,
            title=mapped.title,
            action="created",
            work_id=work.id,
        )

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to ingest {mapped.title}")
        return IngestResult(
            tmdb_id=mapped.tmdb_id,
            title=mapped.title,
            action="error",
            error=str(e),
        )
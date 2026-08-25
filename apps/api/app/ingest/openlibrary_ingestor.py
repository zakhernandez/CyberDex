"""Ingests mapped OpenLibrary data into the database, idempotently."""

import logging
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.openlibrary_mapper import MappedBook
from app.models import (
    Book,
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
    openlibrary_id: str
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


def _find_or_create_creator(db: Session, name: str) -> Creator:
    """Look up an author by slug; create if not found."""
    slug = _slugify(name)
    stmt = select(Creator).where(Creator.slug == slug)
    existing = db.scalars(stmt).first()
    if existing:
        return existing
    creator = Creator(name=name, kind=CreatorKind.PERSON, slug=slug)
    db.add(creator)
    db.flush()
    return creator


def _work_exists_for_openlibrary(db: Session, ol_id: str) -> Work | None:
    """Check if we've already ingested this OpenLibrary work."""
    stmt = (
        select(Work)
        .join(ExternalId, ExternalId.work_id == Work.id)
        .where(
            ExternalId.source == ExternalSource.OPENLIBRARY,
            ExternalId.external_id == ol_id,
        )
    )
    return db.scalars(stmt).first()


def _resolve_slug_collision(db: Session, base_slug: str) -> str:
    """
    If the base slug is taken by another work, append -alt, -alt2, etc.
    Books have more slug collisions than films because multiple books
    can share a title.
    """
    slug = base_slug
    suffix = 1
    while True:
        stmt = select(Work).where(Work.slug == slug)
        if db.scalars(stmt).first() is None:
            return slug
        suffix += 1
        slug = f"{base_slug}-alt{suffix - 1}"


def ingest_book(db: Session, mapped: MappedBook) -> IngestResult:
    """Insert one mapped book into the database. Idempotent by OpenLibrary ID."""

    existing = _work_exists_for_openlibrary(db, mapped.openlibrary_id)
    if existing:
        return IngestResult(
            openlibrary_id=mapped.openlibrary_id,
            title=mapped.title,
            action="skipped_existing",
            work_id=existing.id,
        )

    try:
        # Ensure the slug is unique
        slug = _resolve_slug_collision(db, mapped.slug)

        # Create the base work
        work = Work(
            kind=WorkKind.BOOK,
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

        # Create the book-specific record
        book = Book(
            work_id=work.id,
            page_count=mapped.page_count,
            isbn_13=mapped.isbn_13,
        )
        db.add(book)

        # External ID
        db.add(ExternalId(
            work_id=work.id,
            source=ExternalSource.OPENLIBRARY,
            external_id=mapped.openlibrary_id,
            url=f"https://openlibrary.org/works/{mapped.openlibrary_id}",
        ))

        # Creators (authors)
        for mapped_creator in mapped.creators:
            creator = _find_or_create_creator(db, mapped_creator.name)
            existing_wc = db.get(
                WorkCreator, (work.id, creator.id, CreatorRole.AUTHOR)
            )
            if existing_wc is None:
                db.add(WorkCreator(
                    work_id=work.id,
                    creator_id=creator.id,
                    role=CreatorRole.AUTHOR,
                    credit_order=mapped_creator.credit_order,
                ))

        db.commit()
        return IngestResult(
            openlibrary_id=mapped.openlibrary_id,
            title=mapped.title,
            action="created",
            work_id=work.id,
        )

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to ingest {mapped.title}")
        return IngestResult(
            openlibrary_id=mapped.openlibrary_id,
            title=mapped.title,
            action="error",
            error=str(e),
        )
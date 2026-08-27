"""Endpoints for browsing and viewing works."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Work, WorkKind
from app.schemas import (
    WorkDetail,
    WorkListItem,
    WorkListResponse,
)


router = APIRouter(prefix="/api/works", tags=["works"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=WorkListResponse)
def list_works(
    db: DbSession,
    kind: WorkKind | None = Query(None, description="Filter by kind"),
    q: str | None = Query(None, description="Search in title"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
) -> WorkListResponse:
    """List works with pagination and optional filters."""
    stmt = select(Work)
    count_stmt = select(func.count()).select_from(Work)

    if kind is not None:
        stmt = stmt.where(Work.kind == kind)
        count_stmt = count_stmt.where(Work.kind == kind)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Work.title.ilike(pattern))
        count_stmt = count_stmt.where(Work.title.ilike(pattern))

    total = db.scalar(count_stmt) or 0

    # Order: works with covers first, then by year desc, then by sort_title

    stmt = (
        stmt.order_by(
            Work.cover_url.is_(None),  # False (has cover) sorts before True
            Work.year.desc().nullslast(),
            Work.sort_title,
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    

    items = list(db.scalars(stmt))
    return WorkListResponse(
        items=[WorkListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
    )


@router.get("/{slug}", response_model=WorkDetail)
def get_work(slug: str, db: DbSession) -> WorkDetail:
    """Get one work by slug with all details."""
    stmt = (
        select(Work)
        .where(Work.slug == slug)
        .options(
            selectinload(Work.film),
            selectinload(Work.book),
            selectinload(Work.anime),
            selectinload(Work.external_ids),
            selectinload(Work.creators),
        )
    )
    work = db.scalars(stmt).first()
    if work is None:
        raise HTTPException(status_code=404, detail=f"Work not found: {slug}")

    # We need to explicitly load the Creator for each WorkCreator
    # to avoid N+1 queries
    for wc in work.creators:
        _ = wc.creator  # touch to trigger lazy load; selectinload above didn't cover this

    return WorkDetail.model_validate(work)








'''stmt = (
        select(Work)
        .where(Work.slug == slug)
        .options(
            selectinload(Work.film),
            selectinload(Work.book),
            selectinload(Work.anime),
            selectinload(Work.external_ids),
            selectinload(Work.creators).selectinload(WorkCreator.creator),
        )
    )'''
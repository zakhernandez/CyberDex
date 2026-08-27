"""Endpoints for catalog-level statistics."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Creator, Rating, Work
from app.schemas import CatalogStats, KindCount


router = APIRouter(prefix="/api/stats", tags=["stats"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=CatalogStats)
def get_catalog_stats(db: DbSession) -> CatalogStats:
    """Overall catalog statistics — for the home page."""
    total_works = db.scalar(select(func.count()).select_from(Work)) or 0
    total_creators = db.scalar(select(func.count()).select_from(Creator)) or 0
    total_ratings = db.scalar(select(func.count()).select_from(Rating)) or 0

    stmt = (
        select(Work.kind, func.count().label("count"))
        .group_by(Work.kind)
        .order_by(Work.kind)
    )
    rows = db.execute(stmt).all()
    by_kind = [KindCount(kind=row.kind, count=row.count) for row in rows]

    return CatalogStats(
        total_works=total_works,
        total_creators=total_creators,
        total_ratings=total_ratings,
        by_kind=by_kind,
    )
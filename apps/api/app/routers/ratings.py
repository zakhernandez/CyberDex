"""Endpoints for rating works."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Rating, User, Work
from app.schemas import RatingCreate, RatingRead, RatingWithWork


router = APIRouter(prefix="/api/ratings", tags=["ratings"])

DbSession = Annotated[Session, Depends(get_db)]


def _get_or_create_dev_user(db: Session) -> User:
    """
    TEMPORARY: return a fixed 'dev' user for all requests.
    Will be replaced with real auth in the next block.
    """
    stmt = select(User).where(User.username == "dev")
    user = db.scalars(stmt).first()
    if user is None:
        user = User(username="dev", email="dev@localhost", display_name="Dev User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("", response_model=list[RatingWithWork])
def list_ratings(db: DbSession, limit: int = 50) -> list[RatingWithWork]:
    """List the current user's ratings, most recent first."""
    user = _get_or_create_dev_user(db)
    stmt = (
        select(Rating)
        .where(Rating.user_id == user.id)
        .order_by(Rating.updated_at.desc())
        .limit(limit)
        .options(selectinload(Rating.work))
    )
    ratings = list(db.scalars(stmt))
    return [RatingWithWork.model_validate(r) for r in ratings]


@router.post("", response_model=RatingRead, status_code=201)
def create_or_update_rating(payload: RatingCreate, db: DbSession) -> Rating:
    """Rate a work. If the user has already rated it, update the score."""
    user = _get_or_create_dev_user(db)

    # Verify the work exists
    work = db.get(Work, payload.work_id)
    if work is None:
        raise HTTPException(status_code=404, detail=f"Work not found: {payload.work_id}")

    # Look for existing rating
    stmt = select(Rating).where(
        Rating.user_id == user.id,
        Rating.work_id == payload.work_id,
    )
    existing = db.scalars(stmt).first()

    if existing:
        existing.score = payload.score
        db.commit()
        db.refresh(existing)
        return existing

    rating = Rating(
        user_id=user.id,
        work_id=payload.work_id,
        score=payload.score,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.delete("/{work_id}", status_code=204)
def delete_rating(work_id: int, db: DbSession) -> None:
    """Remove the user's rating of a work."""
    user = _get_or_create_dev_user(db)
    stmt = select(Rating).where(
        Rating.user_id == user.id,
        Rating.work_id == work_id,
    )
    rating = db.scalars(stmt).first()
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(rating)
    db.commit()
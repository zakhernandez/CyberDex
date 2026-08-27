"""Authentication dependency — verifies JWT and returns the current user."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User


DbSession = Annotated[Session, Depends(get_db)]


def _decode_token(token: str) -> dict:
    """
    Decode the JWT from Auth.js.

    Auth.js v5 uses A256CBC-HS512 encrypted JWTs by default.
    """
    try:
        # Auth.js encrypts tokens by default; we need to decrypt not just verify.
        # For learning simplicity, we use HS256 signed tokens instead.
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=["HS256", "HS512"],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid auth token: {e}",
        )


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Extract the JWT from the Authorization header, verify it,
    and return (or create) the corresponding User.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
        )

    token = authorization[len("Bearer "):]
    payload = _decode_token(token)

    google_id = payload.get("googleId")
    email = payload.get("email")
    name = payload.get("name")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required user fields",
        )

    stmt = select(User).where(User.email == email)
    user = db.scalars(stmt).first()

    if user is None:
        # First-time login — create the user
        username = email.split("@")[0]
        # Ensure uniqueness with a suffix if needed
        base_username = username
        suffix = 1
        while db.scalars(select(User).where(User.username == username)).first():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User(
            username=username,
            email=email,
            display_name=name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
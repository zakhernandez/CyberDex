from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ──────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────


class WorkKind(str, Enum):
    FILM = "FILM"
    BOOK = "BOOK"
    ANIME = "ANIME"


class CreatorKind(str, Enum):
    PERSON = "PERSON"
    STUDIO = "STUDIO"


class CreatorRole(str, Enum):
    DIRECTOR = "DIRECTOR"
    SCREENWRITER = "SCREENWRITER"
    AUTHOR = "AUTHOR"
    STUDIO = "STUDIO"
    MANGAKA = "MANGAKA"
    NOVELIST = "NOVELIST"
    COMPOSER = "COMPOSER"


class ExternalSource(str, Enum):
    TMDB = "TMDB"
    OPENLIBRARY = "OPENLIBRARY"
    ANILIST = "ANILIST"
    IMDB = "IMDB"
    MAL = "MAL"
    GOOGLE_BOOKS = "GOOGLE_BOOKS"


class AnimeFormat(str, Enum):
    TV = "TV"
    OVA = "OVA"
    ONA = "ONA"
    FILM = "FILM"
    SPECIAL = "SPECIAL"
    MUSIC = "MUSIC"
    TV_SHORT = "TV_SHORT"


class AnimeSource(str, Enum):
    MANGA = "MANGA"
    LIGHT_NOVEL = "LIGHT_NOVEL"
    ORIGINAL = "ORIGINAL"
    VIDEO_GAME = "VIDEO_GAME"
    NOVEL = "NOVEL"
    OTHER = "OTHER"


class RelationshipType(str, Enum):
    BASED_ON = "BASED_ON"
    ADAPTED_FROM = "ADAPTED_FROM"
    SEQUEL_OF = "SEQUEL_OF"
    PREQUEL_OF = "PREQUEL_OF"
    RELATED = "RELATED"
    REMAKE_OF = "REMAKE_OF"
    SPINOFF_OF = "SPINOFF_OF"


# ──────────────────────────────────────────────────────────────────
# Core catalog
# ──────────────────────────────────────────────────────────────────


class Work(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[WorkKind] = mapped_column(SAEnum(WorkKind, name="work_kind"), index=True)
    title: Mapped[str] = mapped_column(Text)
    original_title: Mapped[str | None] = mapped_column(Text)
    original_language: Mapped[str | None] = mapped_column(String(10))
    sort_title: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    synopsis: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    film: Mapped["Film | None"] = relationship(back_populates="work", uselist=False)
    book: Mapped["Book | None"] = relationship(back_populates="work", uselist=False)
    anime: Mapped["Anime | None"] = relationship(back_populates="work", uselist=False)
    external_ids: Mapped[list["ExternalId"]] = relationship(back_populates="work")
    themes: Mapped[list["WorkTheme"]] = relationship(back_populates="work")
    creators: Mapped[list["WorkCreator"]] = relationship(back_populates="work")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="work")


class Film(Base):
    __tablename__ = "films"

    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
    )
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    tagline: Mapped[str | None] = mapped_column(Text)

    work: Mapped[Work] = relationship(back_populates="film")


class Book(Base):
    __tablename__ = "books"

    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
    )
    page_count: Mapped[int | None] = mapped_column(Integer)
    isbn_13: Mapped[str | None] = mapped_column(String(13), index=True)

    work: Mapped[Work] = relationship(back_populates="book")


class Anime(Base):
    __tablename__ = "anime"

    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
    )
    episodes: Mapped[int | None] = mapped_column(Integer)
    format: Mapped[AnimeFormat | None] = mapped_column(SAEnum(AnimeFormat, name="anime_format"))
    source: Mapped[AnimeSource | None] = mapped_column(SAEnum(AnimeSource, name="anime_source"))

    work: Mapped[Work] = relationship(back_populates="anime")


# ──────────────────────────────────────────────────────────────────
# Creators
# ──────────────────────────────────────────────────────────────────


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[CreatorKind] = mapped_column(SAEnum(CreatorKind, name="creator_kind"))
    slug: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    works: Mapped[list["WorkCreator"]] = relationship(back_populates="creator")


class WorkCreator(Base):
    __tablename__ = "work_creators"

    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE")
    )
    creator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("creators.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[CreatorRole] = mapped_column(SAEnum(CreatorRole, name="creator_role"))
    credit_order: Mapped[int | None] = mapped_column(SmallInteger)

    work: Mapped[Work] = relationship(back_populates="creators")
    creator: Mapped[Creator] = relationship(back_populates="works")

    __table_args__ = (
        PrimaryKeyConstraint("work_id", "creator_id", "role"),
    )


# ──────────────────────────────────────────────────────────────────
# External IDs
# ──────────────────────────────────────────────────────────────────


class ExternalId(Base):
    __tablename__ = "external_ids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[ExternalSource] = mapped_column(SAEnum(ExternalSource, name="external_source"))
    external_id: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)

    work: Mapped[Work] = relationship(back_populates="external_ids")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_external_source_id"),
    )


# ──────────────────────────────────────────────────────────────────
# Themes
# ──────────────────────────────────────────────────────────────────


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("themes.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent: Mapped["Theme | None"] = relationship(remote_side="Theme.id", backref="children")
    works: Mapped[list["WorkTheme"]] = relationship(back_populates="theme")


class WorkTheme(Base):
    __tablename__ = "work_themes"

    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE")
    )
    theme_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("themes.id", ondelete="CASCADE"), index=True
    )
    relevance: Mapped[int | None] = mapped_column(SmallInteger)

    work: Mapped[Work] = relationship(back_populates="themes")
    theme: Mapped[Theme] = relationship(back_populates="works")

    __table_args__ = (
        PrimaryKeyConstraint("work_id", "theme_id"),
    )


# ──────────────────────────────────────────────────────────────────
# Users and ratings
# ──────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ratings: Mapped[list["Rating"]] = relationship(back_populates="user")


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="ratings")
    work: Mapped[Work] = relationship(back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "work_id", name="uq_user_work_rating"),
        CheckConstraint("score BETWEEN 1 AND 10", name="ck_rating_score_range"),
        Index("ix_ratings_user_created", "user_id", "created_at"),
    )


# ──────────────────────────────────────────────────────────────────
# Work relationships
# ──────────────────────────────────────────────────────────────────


class WorkRelationship(Base):
    __tablename__ = "work_relationships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    from_work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), index=True
    )
    to_work_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("works.id", ondelete="CASCADE"), index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SAEnum(RelationshipType, name="relationship_type")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "from_work_id", "to_work_id", "relationship_type",
            name="uq_work_relationship",
        ),
    )
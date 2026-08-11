from __future__ import annotations

from datetime import datetime

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str | None] = mapped_column(String, index=True)

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    
    # Organizer contact information
    organizer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    organizer_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    organizer_email: Mapped[str | None] = mapped_column(String, nullable=True)
    organizer_inn: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    
    # New flexible field for site-specific data
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    title_hash: Mapped[str] = mapped_column(String, unique=False, index=True)
    compound_hash: Mapped[str] = mapped_column(String, unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matches: Mapped[list[TenderKeywordMatch]] = relationship(back_populates="tender", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_tenders_source_external_id"),
    )


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phrase: Mapped[str] = mapped_column(String, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_blacklist: Mapped[bool] = mapped_column(default=False)

    matches: Mapped[list[TenderKeywordMatch]] = relationship(back_populates="keyword", cascade="all, delete-orphan")


class TenderKeywordMatch(Base):
    __tablename__ = "tender_keyword_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)

    tender: Mapped[Tender] = relationship(back_populates="matches")
    keyword: Mapped[Keyword] = relationship(back_populates="matches")

    __table_args__ = (
        UniqueConstraint("tender_id", "keyword_id", name="uq_tender_keyword"),
    )


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

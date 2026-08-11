from __future__ import annotations

from datetime import datetime

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Winner(Base):
    __tablename__ = "winners"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String, index=True)
    tender_id: Mapped[str] = mapped_column(String, index=True)  # Reference to original tender
    tender_url: Mapped[str] = mapped_column(String)
    
    # Winner company information
    company_name: Mapped[str] = mapped_column(String, index=True)
    company_inn: Mapped[str | None] = mapped_column(String, index=True)  # STIR/INN
    company_address: Mapped[str | None] = mapped_column(Text)
    company_phone: Mapped[str | None] = mapped_column(String)
    company_email: Mapped[str | None] = mapped_column(String)
    company_website: Mapped[str | None] = mapped_column(String)
    
    # Tender result information
    tender_amount: Mapped[str | None] = mapped_column(String)  # Winning amount
    tender_date: Mapped[datetime | None] = mapped_column(DateTime)
    winner_announcement_date: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Additional details
    contract_details: Mapped[str | None] = mapped_column(Text)
    competition_type: Mapped[str | None] = mapped_column(String)  # Open tender, closed tender, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source", "tender_id", name="uq_winners_source_tender_id"),
        UniqueConstraint("company_inn", "tender_date", name="uq_winners_company_date"),
    )


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Company identification
    company_name: Mapped[str] = mapped_column(String, index=True)
    company_inn: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    
    # Contact information
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(Text)
    
    # Business information
    business_type: Mapped[str | None] = mapped_column(String)  # Construction, IT, Agriculture, etc.
    specialization: Mapped[str | None] = mapped_column(Text)  # Areas of expertise
    
    # Statistics
    total_wins: Mapped[int] = mapped_column(Integer, default=0)
    total_amount_won: Mapped[str | None] = mapped_column(String)  # Sum of all won tenders
    first_win_date: Mapped[datetime | None] = mapped_column(DateTime)
    last_win_date: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Enrichment status
    is_enriched: Mapped[bool] = mapped_column(default=False)
    enrichment_date: Mapped[datetime | None] = mapped_column(DateTime)
    enrichment_sources: Mapped[str | None] = mapped_column(Text)  # JSON of sources used
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_inn", name="uq_company_profiles_inn"),
    )

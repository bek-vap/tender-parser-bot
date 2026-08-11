from __future__ import annotations
from datetime import datetime
import uuid
from sqlalchemy import DateTime, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

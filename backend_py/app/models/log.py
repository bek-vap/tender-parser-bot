from __future__ import annotations

from datetime import datetime

import uuid

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParserLog(Base):
    __tablename__ = "parser_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)  # started, completed, failed, captcha_detected, new_tender_found, duplicate_skipped
    message: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)  # JSON string for additional data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[int | None] = mapped_column(default=None)
    items_processed: Mapped[int | None] = mapped_column(default=None)
    items_found: Mapped[int | None] = mapped_column(default=None)
    items_skipped: Mapped[int | None] = mapped_column(default=None)  # Number of duplicates skipped
    captcha_detected: Mapped[bool] = mapped_column(default=False)
    error_traceback: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<ParserLog {self.task_name}: {self.status}>"

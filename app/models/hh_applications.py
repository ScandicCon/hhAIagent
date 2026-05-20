from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HhApplication(Base):
    __tablename__ = "hh_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    vacancy_hh_id: Mapped[str] = mapped_column(String(32), index=True)
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("vacancy_analyses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="applied", nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

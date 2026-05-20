from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base

class CoverLetter(Base):
    __tablename__ = "cover_letters"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("vacancy_analyses.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analysis = relationship(
        "VacancyAnalysis",
        back_populates="cover_letters"
    )
    cover_letter_versions = relationship(
    "CoverLetterVersion",
    back_populates="cover_letter"
)
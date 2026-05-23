from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, DateTime
from app.db.base import Base
from datetime import datetime

class VacancyAnalysis(Base):
    __tablename__ = "vacancy_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id"), nullable=False, index=True
    )
    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id"), nullable=False, index=True
    )
    match_score: Mapped[int] = mapped_column(nullable=False)
    should_apply: Mapped[bool] = mapped_column(nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    pros: Mapped[str] = mapped_column(Text, nullable=False)
    cons: Mapped[str] =  mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile = relationship("Profile", back_populates="vacancy_analyses")
    vacancy  = relationship("Vacancy", back_populates="vacancy_analyses")
    cover_letters = relationship(
    "CoverLetter",
    back_populates="analysis"
)
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.services.plans import PLAN_FREE


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[str] = mapped_column(String(20), default=PLAN_FREE, nullable=False)
    searches_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cover_letters_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_week_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_search_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_search_filters: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_digest_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id"), nullable=True)
    bonus_searches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    hh_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    hh_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    hh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hh_resume_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hh_resume_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    apply_mode: Mapped[str] = mapped_column(
        String(20), default="semi_auto", nullable=False
    )
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applications_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_day: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    vacancy_analyses = relationship("VacancyAnalysis", back_populates="profile")
    resume_versions = relationship("ResumeVersion", back_populates="profile")

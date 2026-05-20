from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, DateTime, ForeignKey
from datetime import datetime

class CoverLetterVersion(Base):
    __tablename__ = "cover_letter_versions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cover_letter_id: Mapped[int] = mapped_column(ForeignKey("cover_letters.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cover_letter = relationship(
    "CoverLetter",
    back_populates="cover_letter_versions"
)
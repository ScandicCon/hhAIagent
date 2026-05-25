from app.db.base import Base
from app.db.migrate import migrate_all
from app.models import hh_applications  # noqa: F401
from app.models import payments  # noqa: F401
from app.db.session import engine

from app.models import (  # noqa: F401
    cover_letter_versions,
    cover_letters,
    profiles,
    resume_versions,
    vacancies,
    vacancy_analyses,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_all()

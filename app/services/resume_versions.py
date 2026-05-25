from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resume_versions import ResumeVersion

MAX_VERSIONS_PER_PROFILE = 20


def archive_current_resume(profile_id: int, resume_text: str, session: Session) -> None:
    session.add(
        ResumeVersion(
            profile_id=profile_id,
            resume_text=resume_text,
        )
    )
    session.flush()

    rows = session.execute(
        select(ResumeVersion.id)
        .where(ResumeVersion.profile_id == profile_id)
        .order_by(ResumeVersion.created_at.desc())
        .offset(MAX_VERSIONS_PER_PROFILE)
    ).all()
    for (version_id,) in rows:
        old = session.get(ResumeVersion, version_id)
        if old is not None:
            session.delete(old)


def list_resume_versions(profile_id: int, session: Session) -> list[ResumeVersion]:
    stmt = (
        select(ResumeVersion)
        .where(ResumeVersion.profile_id == profile_id)
        .order_by(ResumeVersion.created_at.desc())
        .limit(MAX_VERSIONS_PER_PROFILE)
    )
    return list(session.execute(stmt).scalars().all())

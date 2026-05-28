import logging

from sqlalchemy import inspect, select, text

from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)

PROFILE_COLUMNS = {
    "plan": "VARCHAR(20) NOT NULL DEFAULT 'free'",
    "searches_this_week": "INTEGER NOT NULL DEFAULT 0",
    "cover_letters_this_week": "INTEGER NOT NULL DEFAULT 0",
    "usage_week_start": "DATETIME",
    "digest_enabled": "BOOLEAN NOT NULL DEFAULT 0",
    "last_search_query": "TEXT",
    "last_search_filters": "TEXT",
    "last_digest_at": "DATETIME",
    "referral_code": "VARCHAR(16)",
    "referred_by_id": "INTEGER",
    "bonus_searches": "INTEGER NOT NULL DEFAULT 0",
    "referral_applied": "BOOLEAN NOT NULL DEFAULT 0",
    "hh_access_token": "TEXT",
    "hh_refresh_token": "TEXT",
    "hh_token_expires_at": "DATETIME",
    "hh_resume_id": "VARCHAR(64)",
    "hh_resume_title": "VARCHAR(255)",
    "apply_mode": "VARCHAR(20) NOT NULL DEFAULT 'semi_auto'",
    "auto_apply_enabled": "BOOLEAN NOT NULL DEFAULT 0",
    "applications_today": "INTEGER NOT NULL DEFAULT 0",
    "applications_day": "DATETIME",
}


def _migrate_table(table: str, columns: dict) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns(table)}

    with engine.begin() as connection:
        for name, ddl in columns.items():
            if name in existing:
                continue
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def migrate_profiles_table() -> None:
    _migrate_table("profiles", PROFILE_COLUMNS)


def migrate_apply_mode_defaults() -> None:
    inspector = inspect(engine)
    if "profiles" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("profiles")}
    if "apply_mode" not in columns:
        return

    from app.models.profiles import Profile
    from app.services.apply_modes import APPLY_MODE_AUTO

    with SessionLocal() as session:
        profiles = session.execute(
            select(Profile).where(Profile.auto_apply_enabled.is_(True))
        ).scalars().all()
        for profile in profiles:
            if profile.apply_mode != APPLY_MODE_AUTO:
                profile.apply_mode = APPLY_MODE_AUTO
        session.commit()


def migrate_all() -> None:
    migrate_profiles_table()
    try:
        migrate_apply_mode_defaults()
    except Exception:
        logger.exception("migrate_apply_mode_defaults skipped")

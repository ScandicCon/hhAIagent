import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config.settings import DATABASE_URL

_engine_kwargs: dict = {}
_connect_args: dict = {}

if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    _connect_args["timeout"] = 30
    _engine_kwargs["connect_args"] = _connect_args
else:
    _engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        }
    )

engine = create_engine(DATABASE_URL, **_engine_kwargs)


@event.listens_for(engine, "connect")
def _sqlite_pragma(dbapi_connection, connection_record):
    if not DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

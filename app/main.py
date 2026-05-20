import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import APIStatusError, RateLimitError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import API_HOST, API_PORT, BACKEND_URL, DATABASE_URL
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine
from app.routers.auth import router as auth_router
from app.routers.hh import router as hh_router
from app.routers.profiles import router as profiles_router
from app.routers.landing import router as landing_router
from app.routers.payments import router as payments_router
from app.routers.referrals import router as referrals_router
from app.routers.subscription import router as subscription_router
from app.routers.vacancies import router as vacancies_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("HH AI backend ready")
    logger.info("URL: %s", BACKEND_URL)
    logger.info("Database: %s", DATABASE_URL)
    yield


app = FastAPI(title="HH AI Backend", lifespan=lifespan)

app.include_router(vacancies_router)
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(subscription_router)
app.include_router(landing_router)
app.include_router(payments_router)
app.include_router(referrals_router)
app.include_router(hh_router)


@app.get("/")
def root():
    return {
        "app": "hh-ai-backend",
        "ok": True,
        "url": BACKEND_URL,
        "host": API_HOST,
        "port": API_PORT,
    }


@app.get("/health")
def health():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "app": "hh-ai-backend"}
    except SQLAlchemyError as error:
        logger.exception("Health check failed")
        return {
            "status": "error",
            "database": "disconnected",
            "app": "hh-ai-backend",
            "detail": str(error),
        }


@app.exception_handler(RateLimitError)
@app.exception_handler(APIStatusError)
async def ai_rate_limit_handler(request: Request, exc: Exception):
    status = getattr(exc, "status_code", 429)
    if status != 429:
        raise exc
    logger.exception("AI rate limit on %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "AI временно перегружен (лимит OpenRouter). Попробуй через 1-2 минуты.",
            "code": "ai_rate_limit",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error", "message": str(exc)},
    )

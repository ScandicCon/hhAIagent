from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["landing"])

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@router.get("/welcome")
def welcome_page():
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/requisites")
def requisites_page():
    return FileResponse(STATIC_DIR / "requisites.html")

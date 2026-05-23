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


@router.get("/pay")
def pay_page():
    return FileResponse(STATIC_DIR / "pay.html")


@router.get("/assets/site.css")
def site_styles():
    return FileResponse(STATIC_DIR / "site.css", media_type="text/css")


@router.get("/assets/site.js")
def site_scripts():
    return FileResponse(STATIC_DIR / "site.js", media_type="application/javascript")

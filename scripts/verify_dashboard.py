"""Smoke-check dashboard modules import."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.apply_modes import set_apply_mode  # noqa: E402
from app.services.dashboard_stats import build_dashboard_stats  # noqa: E402
from app.services.web_auth import verify_telegram_login  # noqa: E402
from app.main import app  # noqa: E402

routes = [r.path for r in app.routes if hasattr(r, "path")]
required = [
    "/app",
    "/web/config",
    "/web/auth/telegram",
    "/web/auth/me",
    "/dashboard/stats",
    "/dashboard/vacancies",
    "/dashboard/mode",
    "/dashboard/search",
    "/dashboard/applications/batch",
]
missing = [p for p in required if p not in routes]
if missing:
    print("MISSING ROUTES:", missing)
    sys.exit(1)

print("OK: dashboard routes registered:", len(required))
print("OK: imports")

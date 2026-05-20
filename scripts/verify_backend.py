"""Check backend: root + health + profile upsert."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from app.config.settings import BACKEND_URL


def main() -> int:
    print(f"Backend URL: {BACKEND_URL}")

    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            root = client.get(f"{BACKEND_URL}/")
            print(f"GET / -> {root.status_code} {root.text[:120]}")

            if root.status_code != 200 or "hh-ai-backend" not in root.text:
                print("ERROR: not our FastAPI on this port.")
                print("Keep run_backend.ps1 running, then retry.")
                return 1

            health = client.get(f"{BACKEND_URL}/health")
            print(f"GET /health -> {health.status_code} {health.text}")

            upsert = client.post(
                f"{BACKEND_URL}/profiles/upsert",
                json={
                    "name": "__verify__",
                    "resume_text": "verify backend connection " + "x" * 10,
                    "skills": "verify",
                },
            )
            print(f"POST /profiles/upsert -> {upsert.status_code} {upsert.text[:120]}")

            if upsert.status_code != 200:
                print("ERROR: upsert failed")
                return 1

    except httpx.RequestError as error:
        print(f"ERROR: cannot connect: {error}")
        return 1

    print("OK: backend works")
    return 0


if __name__ == "__main__":
    sys.exit(main())

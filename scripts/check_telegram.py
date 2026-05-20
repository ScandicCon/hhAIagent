"""Check access to Telegram Bot API."""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROXY = (os.getenv("TELEGRAM_PROXY") or "").strip() or None
TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

if not TOKEN:
    print("ERROR: BOT_TOKEN not set in .env")
    sys.exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getMe"
print(f"GET {url.split(TOKEN)[0]}.../getMe")
if PROXY:
    print(f"Proxy: {PROXY}")

try:
    with httpx.Client(timeout=15, trust_env=False, proxy=PROXY) as client:
        response = client.get(url)
    print(f"Status: {response.status_code}")
    print(response.text[:300])
    sys.exit(0 if response.status_code == 200 else 1)
except httpx.RequestError as error:
    print(f"ERROR: {error}")
    print()
    print("Telegram API is not reachable from this PC.")
    print("Try: VPN, or TELEGRAM_PROXY=socks5://127.0.0.1:1080 in .env")
    sys.exit(1)

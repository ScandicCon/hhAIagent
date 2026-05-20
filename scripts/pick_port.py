"""Выбирает порт для нашего API и обновляет .env."""
import re
import socket
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
CANDIDATES = [9090, 18080, 5050, 8888, 8080, 8000]


def is_our_backend(port: int) -> bool:
    try:
        response = httpx.get(
            f"http://127.0.0.1:{port}/",
            timeout=2,
            trust_env=False,
        )
        return response.status_code == 200 and "hh-ai-backend" in response.text
    except httpx.HTTPError:
        return False


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def pick_port() -> int | None:
    for port in CANDIDATES:
        if is_our_backend(port):
            return port
        if port_is_free(port):
            return port
    return None


def update_env(port: int) -> None:
    url = f"http://127.0.0.1:{port}"
    lines: list[str] = []

    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    def set_key(key: str, value: str) -> None:
        nonlocal lines
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        replaced = False
        for index, line in enumerate(lines):
            if pattern.match(line):
                lines[index] = f"{key}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{key}={value}")

    set_key("API_HOST", "127.0.0.1")
    set_key("API_PORT", str(port))
    set_key("BACKEND_URL", url)

    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: API_PORT={port}, BACKEND_URL={url}")


def main() -> int:
    port = pick_port()
    if port is None:
        print("ERROR: нет свободного порта.", file=sys.stderr)
        print("Закрой лишние программы или перезагрузи ПК.", file=sys.stderr)
        return 1

    update_env(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())

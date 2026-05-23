import httpx

DEFAULT_TIMEOUT = httpx.Timeout(30.0)
LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=30)

_shared_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            trust_env=False,
            limits=LIMITS,
            timeout=DEFAULT_TIMEOUT,
        )
    return _shared_client


async def close_http_client() -> None:
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None


def async_client(**kwargs) -> httpx.AsyncClient:
    """Совместимость: для нового кода используйте get_http_client() + timeout= на запросе."""
    timeout = kwargs.pop("timeout", None)
    if timeout is not None and not kwargs:
        return httpx.AsyncClient(trust_env=False, timeout=timeout)
    return httpx.AsyncClient(trust_env=False, **kwargs)

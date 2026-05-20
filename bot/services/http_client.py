import httpx

# Windows often has HTTP_PROXY set; localhost must bypass it.
LOCAL_CLIENT_KWARGS = {
    "trust_env": False,
    "timeout": httpx.Timeout(30.0),
}


def async_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(trust_env=False, **kwargs)


def sync_client(**kwargs) -> httpx.Client:
    return httpx.Client(trust_env=False, **kwargs)

import asyncio
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException, status

from bitnp_ideas.core.config import settings

# ---------------------------------------------------------------------------
# Shared HTTP client with connection pooling (reused across all auth calls)
# ---------------------------------------------------------------------------
_http_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Discovery metadata cache (TTL-based) —
# avoids re-fetching /.well-known/openid-configuration on every call
# ---------------------------------------------------------------------------
_metadata_cache: dict | None = None
_metadata_cache_ts: float = 0.0
_metadata_cache_ttl: float = 3600.0  # 1 hour
_metadata_cache_lock = asyncio.Lock()


async def _get_http_client() -> httpx.AsyncClient:
    """Return a session-scoped httpx client with connection pooling."""
    global _http_client
    if _http_client is None:
        async with _client_lock:
            if _http_client is None:
                _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    return _http_client


async def _get_metadata(client: httpx.AsyncClient, discovery_url: str) -> dict:
    """Fetch and cache the OIDC discovery document."""
    global _metadata_cache, _metadata_cache_ts

    async with _metadata_cache_lock:
        now = time.monotonic()
        if _metadata_cache is not None and (now - _metadata_cache_ts) < _metadata_cache_ttl:
            return _metadata_cache

    response = await client.get(discovery_url)
    response.raise_for_status()
    data: dict = response.json()

    async with _metadata_cache_lock:
        _metadata_cache = data
        _metadata_cache_ts = time.monotonic()

    return data


@dataclass(frozen=True)
class OidcLoginRequest:
    authorization_url: str
    state: str


class OidcAdapter:
    def discovery_url(self) -> str:
        if not settings.security.oidc.issuer_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC provider is not configured.",
            )
        issuer = str(settings.security.oidc.issuer_url).rstrip("/")
        if issuer.endswith("/.well-known/openid-configuration"):
            return issuer
        return f"{issuer}/.well-known/openid-configuration"

    async def load_metadata(self) -> dict:
        """Return cached OIDC discovery metadata (5-min TTL)."""
        if not settings.security.oidc.enabled:
            return {}
        client = await _get_http_client()
        return await _get_metadata(client, self.discovery_url())

    async def build_login_request(self, state: str, redirect_uri: str) -> OidcLoginRequest:
        if not settings.security.oidc.enabled:
            return OidcLoginRequest(authorization_url="/auth/me", state=state)

        metadata = await self.load_metadata()
        authorization_endpoint = metadata.get("authorization_endpoint")
        if not authorization_endpoint:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC authorization endpoint is unavailable.",
            )

        query = urlencode(
            {
                "client_id": settings.security.oidc.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
            }
        )
        authorization_url = f"{authorization_endpoint}?{query}"
        return OidcLoginRequest(authorization_url=authorization_url, state=state)

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        metadata = await self.load_metadata()
        token_endpoint = metadata.get("token_endpoint")
        if not token_endpoint:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC token endpoint is unavailable.",
            )

        client = await _get_http_client()
        response = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.security.oidc.client_id,
                "client_secret": settings.security.oidc.client_secret,
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OIDC code exchange failed.",
            )
        return response.json()

    async def userinfo(self, access_token: str) -> dict:
        metadata = await self.load_metadata()
        userinfo_endpoint = metadata.get("userinfo_endpoint")
        if not userinfo_endpoint:
            claims = jwt.decode(access_token, options={"verify_signature": False})
            return claims

        client = await _get_http_client()
        response = await client.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


oidc_adapter = OidcAdapter()

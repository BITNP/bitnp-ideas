from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException, status

from bitnp_ideas.core.config import settings


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
        if not settings.security.oidc.enabled:
            return {}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.discovery_url())
            response.raise_for_status()
            return response.json()

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

        async with httpx.AsyncClient(timeout=10) as client:
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

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()


oidc_adapter = OidcAdapter()

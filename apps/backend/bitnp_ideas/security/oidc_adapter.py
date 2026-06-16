from dataclasses import dataclass

from bitnp_ideas.core.config import settings


@dataclass(frozen=True)
class OidcLoginRequest:
    authorization_url: str
    state: str


class OidcAdapter:
    def build_login_request(self, state: str, redirect_uri: str) -> OidcLoginRequest:
        if not settings.oidc_issuer_url or not settings.oidc_client_id:
            return OidcLoginRequest(authorization_url="/auth/me", state=state)

        issuer = str(settings.oidc_issuer_url).rstrip("/")
        authorization_url = (
            f"{issuer}/protocol/openid-connect/auth"
            f"?client_id={settings.oidc_client_id}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code&scope=openid%20email%20profile"
            f"&state={state}"
        )
        return OidcLoginRequest(authorization_url=authorization_url, state=state)


oidc_adapter = OidcAdapter()

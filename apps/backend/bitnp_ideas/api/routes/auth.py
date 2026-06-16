from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends

from bitnp_ideas.schemas.common import CurrentUser
from bitnp_ideas.security.oidc_adapter import oidc_adapter
from bitnp_ideas.security.rbac import get_current_user

router = APIRouter()
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/login")
async def login(redirect_uri: str = "http://localhost:5173/login") -> dict[str, str]:
    request = oidc_adapter.build_login_request(state=token_urlsafe(24), redirect_uri=redirect_uri)
    return {"authorization_url": request.authorization_url, "state": request.state}


@router.get("/callback")
async def callback(code: str, state: str) -> dict[str, str]:
    return {"message": "OIDC callback adapter placeholder", "code": code, "state": state}


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUserDep) -> CurrentUser:
    return user


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"message": "logged out"}

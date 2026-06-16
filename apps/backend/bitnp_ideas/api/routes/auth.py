from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import CurrentUser
from bitnp_ideas.security.oidc_adapter import oidc_adapter
from bitnp_ideas.security.rbac import create_session_token, find_superusers, get_current_user
from bitnp_ideas.services.backend import utcnow

router = APIRouter()
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/login")
async def login(redirect_uri: str = "http://localhost:5173/login") -> dict[str, str]:
    request = await oidc_adapter.build_login_request(
        state=token_urlsafe(24), redirect_uri=redirect_uri
    )
    return {"authorization_url": request.authorization_url, "state": request.state}


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    session: DbSessionDep,
    redirect_uri: str = "http://localhost:5173/login",
) -> dict[str, object]:
    _ = state
    tokens = await oidc_adapter.exchange_code(code=code, redirect_uri=redirect_uri)
    access_token = tokens.get("access_token")
    if not isinstance(access_token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC access token missing."
        )

    userinfo = await oidc_adapter.userinfo(access_token)
    subject = userinfo.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC subject missing."
        )

    email = userinfo.get("email") or f"{subject}@login.bitnp.net"
    display_name = (
        userinfo.get("name")
        or userinfo.get("preferred_username")
        or userinfo.get("nickname")
        or email
    )

    result = await session.scalars(
        select(User).where(User.sso_provider == "login.bitnp.net", User.sso_subject == subject)
    )
    user = result.one_or_none()
    if user is None:
        role = GlobalRole.SUPERUSER if not await find_superusers(session) else GlobalRole.DEVELOPER
        user = User(
            sso_provider="login.bitnp.net",
            sso_subject=subject,
            email=email,
            display_name=display_name,
            avatar_url=userinfo.get("picture"),
            global_role=role,
            is_active=True,
        )
        session.add(user)
    else:
        user.email = email
        user.display_name = display_name
        user.avatar_url = userinfo.get("picture")
        user.updated_at = utcnow()

    await session.commit()
    await session.refresh(user)
    return {
        "access_token": create_session_token(user),
        "token_type": "bearer",
        "user": CurrentUser.model_validate(user),
    }


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUserDep) -> CurrentUser:
    return user


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"message": "logged out"}

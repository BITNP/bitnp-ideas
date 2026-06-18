import asyncio
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.core.config import settings
from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import ApiMessage, CallbackResponse, CurrentUser, LoginResponse
from bitnp_ideas.security.oidc_adapter import oidc_adapter
from bitnp_ideas.security.rbac import (
    bearer_scheme,
    create_session_token,
    find_superusers,
    get_current_user,
    revoke_session_token,
)
from bitnp_ideas.services.backend import utcnow

router = APIRouter()
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
BearerCredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
OIDC_STATE_KIND = "oidc_state"


async def create_oidc_state(redirect_uri: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "kind": OIDC_STATE_KIND,
        "nonce": token_urlsafe(24),
        "redirect_uri": redirect_uri,
        "iat": now,
        "exp": now + timedelta(seconds=settings.security.oidc_state_ttl_seconds),
    }
    return await asyncio.to_thread(
        jwt.encode, payload, settings.security.session_secret_key, algorithm="HS256"
    )


async def verify_oidc_state(state: str, redirect_uri: str) -> None:
    try:
        payload = await asyncio.to_thread(
            jwt.decode,
            state,
            settings.security.session_secret_key,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC state expired.",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OIDC state.",
        ) from exc

    if payload.get("kind") != OIDC_STATE_KIND or payload.get("redirect_uri") != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OIDC state.",
        )


@router.get("/login", response_model=LoginResponse)
async def login(redirect_uri: str = "http://localhost:5173/login") -> LoginResponse:
    request = await oidc_adapter.build_login_request(
        state=await create_oidc_state(redirect_uri), redirect_uri=redirect_uri
    )
    return LoginResponse(authorization_url=request.authorization_url, state=request.state)


@router.get("/callback", response_model=CallbackResponse)
async def callback(
    code: str,
    state: str,
    session: DbSessionDep,
    redirect_uri: str = "http://localhost:5173/login",
) -> CallbackResponse:
    await verify_oidc_state(state=state, redirect_uri=redirect_uri)
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
    return CallbackResponse(
        access_token=await create_session_token(user),
        token_type="bearer",
        user=CurrentUser.model_validate(user),
    )


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUserDep) -> CurrentUser:
    return user


@router.post("/logout", response_model=ApiMessage)
async def logout(
    user: CurrentUserDep,
    credentials: BearerCredentialsDep,
    session: DbSessionDep,
) -> ApiMessage:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    await revoke_session_token(credentials.credentials, user, session)
    return ApiMessage(message="logged out")

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.core.config import settings
from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ApiKey, SessionTokenRevocation, User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import CurrentUser
from bitnp_ideas.security.api_keys import verify_api_key_request

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user: CurrentUser
    api_key: ApiKey | None = None

    @property
    def is_api_key(self) -> bool:
        return self.api_key is not None


async def create_session_token(user: User) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "jti": token_urlsafe(24),
        "email": user.email,
        "name": user.display_name,
        "role": user.global_role,
        "iat": now,
        "exp": now + timedelta(seconds=settings.security.session_token_ttl_seconds),
    }
    return await asyncio.to_thread(
        jwt.encode, payload, settings.security.session_secret_key, algorithm="HS256"
    )


async def decode_session_token(token: str) -> dict:
    try:
        return await asyncio.to_thread(
            jwt.decode,
            token,
            settings.security.session_secret_key,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from exc


def jwt_timestamp_to_datetime(value: object) -> datetime:
    if not isinstance(value, int | float):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )
    return datetime.fromtimestamp(value, tz=UTC)


def utc_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def _user_from_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
) -> CurrentUser | None:
    if not credentials:
        return None
    if credentials.scheme.lower() != "bearer":
        return None

    payload = await decode_session_token(credentials.credentials)
    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )
    revocation = await session.get(SessionTokenRevocation, jti)
    if revocation is not None and utc_aware(revocation.expires_at) > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has been revoked.",
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token."
        )

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive.")

    return CurrentUser.model_validate(user)


async def revoke_session_token(token: str, user: CurrentUser, session: AsyncSession) -> None:
    payload = await decode_session_token(token)
    jti = payload.get("jti")
    subject = payload.get("sub")
    if not isinstance(jti, str) or subject != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )

    expires_at = jwt_timestamp_to_datetime(payload.get("exp"))
    existing = await session.get(SessionTokenRevocation, jti)
    if existing is None:
        session.add(
            SessionTokenRevocation(
                jti=jti,
                user_id=user.id,
                expires_at=expires_at,
                revoked_at=datetime.now(UTC),
            )
        )
    else:
        existing.expires_at = expires_at
        existing.revoked_at = datetime.now(UTC)
    await session.commit()


async def get_auth_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthContext:
    bearer_user = await _user_from_bearer_token(credentials, session)
    if bearer_user:
        return AuthContext(user=bearer_user)

    api_key = await verify_api_key_request(request, session)
    if api_key:
        user = await session.get(User, api_key.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API key owner inactive."
            )
        return AuthContext(user=CurrentUser.model_validate(user), api_key=api_key)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


async def get_current_user(
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> CurrentUser:
    if context.is_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires a user session.",
        )
    return context.user


async def find_superusers(session: AsyncSession) -> list[User]:
    result = await session.scalars(select(User).where(User.global_role == GlobalRole.SUPERUSER))
    return list(result)


def require_roles(*roles: GlobalRole):
    async def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.global_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient global role for this operation.",
            )
        return user

    return dependency

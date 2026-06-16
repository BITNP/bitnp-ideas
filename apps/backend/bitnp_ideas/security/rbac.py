from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.core.config import settings
from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ApiKey, User
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


def create_session_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.display_name,
        "role": user.global_role,
    }
    return jwt.encode(payload, settings.security.session_secret_key, algorithm="HS256")


async def _user_from_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
) -> CurrentUser | None:
    if not credentials:
        return None
    if credentials.scheme.lower() != "bearer":
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.security.session_secret_key,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token."
        )

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive.")

    return CurrentUser.model_validate(user)


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

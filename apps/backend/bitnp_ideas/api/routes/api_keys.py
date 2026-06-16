from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.core.config import settings
from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ApiKey
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyRead,
    ApiKeyUpdate,
    ApiMessage,
    CurrentUser,
)
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import add_audit, utcnow

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]

ALLOWED_SCOPES = {"ideas:read", "ideas:write"}


def validate_scopes(scopes: list[str]) -> None:
    disallowed = sorted(set(scopes) - ALLOWED_SCOPES)
    if disallowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"API key scopes are limited to ideas:read/write: {', '.join(disallowed)}",
        )


def read_api_key(api_key: ApiKey) -> ApiKeyRead:
    return ApiKeyRead.model_validate(api_key)


async def get_owned_api_key(session: AsyncSession, user: CurrentUser, api_key_id: str) -> ApiKey:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    if user.global_role != GlobalRole.SUPERUSER and api_key.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key access denied.")
    return api_key


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys(user: CurrentUserDep, session: DbSessionDep) -> list[ApiKeyRead]:
    statement = select(ApiKey).order_by(ApiKey.created_at.desc())
    if user.global_role != GlobalRole.SUPERUSER:
        statement = statement.where(ApiKey.user_id == user.id)
    result = await session.scalars(statement)
    return [read_api_key(api_key) for api_key in result]


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    payload: ApiKeyCreate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiKeyCreateResponse:
    validate_scopes(payload.scopes)
    key_id = f"bik_{token_urlsafe(18)}"
    signing_secret = f"biks_{token_urlsafe(32)}"
    api_key = ApiKey(
        user_id=user.id,
        name=payload.name,
        key_id=key_id,
        secret_hash=signing_secret,
        secret_last4=signing_secret[-4:],
        scopes=payload.scopes,
        allowed_entities=settings.api_keys.allowed_entities,
        is_active=True,
        created_at=utcnow(),
    )
    session.add(api_key)
    await session.flush()
    add_audit(
        session,
        actor_user_id=user.id,
        action="api_key.created",
        entity_type="api_key",
        entity_id=api_key.id,
        after={"name": api_key.name, "scopes": api_key.scopes},
    )
    await session.commit()
    await session.refresh(api_key)
    return ApiKeyCreateResponse(api_key=read_api_key(api_key), secret=signing_secret)


@router.patch("/{api_key_id}", response_model=ApiMessage)
async def update_api_key(
    api_key_id: str,
    payload: ApiKeyUpdate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiMessage:
    api_key = await get_owned_api_key(session, user, api_key_id)
    if payload.scopes is not None:
        validate_scopes(payload.scopes)
    before = {"name": api_key.name, "is_active": api_key.is_active, "scopes": api_key.scopes}
    if payload.name is not None:
        api_key.name = payload.name
    if payload.is_active is not None:
        api_key.is_active = payload.is_active
        api_key.revoked_at = None if payload.is_active else utcnow()
    if payload.scopes is not None:
        api_key.scopes = payload.scopes
    add_audit(
        session,
        actor_user_id=user.id,
        action="api_key.updated",
        entity_type="api_key",
        entity_id=api_key.id,
        before=before,
        after=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ApiMessage(message=f"api key {api_key_id} updated")


@router.delete("/{api_key_id}", response_model=ApiMessage)
async def revoke_api_key(
    api_key_id: str, user: CurrentUserDep, session: DbSessionDep
) -> ApiMessage:
    api_key = await get_owned_api_key(session, user, api_key_id)
    api_key.is_active = False
    api_key.revoked_at = utcnow()
    add_audit(
        session,
        actor_user_id=user.id,
        action="api_key.revoked",
        entity_type="api_key",
        entity_id=api_key.id,
    )
    await session.commit()
    return ApiMessage(message=f"api key {api_key_id} revoked")


@router.post("/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    api_key_id: str,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiKeyCreateResponse:
    api_key = await get_owned_api_key(session, user, api_key_id)
    signing_secret = f"biks_{token_urlsafe(32)}"
    before = {"secret_last4": api_key.secret_last4}
    api_key.secret_hash = signing_secret
    api_key.secret_last4 = signing_secret[-4:]
    api_key.is_active = True
    api_key.revoked_at = None
    add_audit(
        session,
        actor_user_id=user.id,
        action="api_key.rotated",
        entity_type="api_key",
        entity_id=api_key.id,
        before=before,
        after={"secret_last4": api_key.secret_last4},
    )
    await session.commit()
    await session.refresh(api_key)
    return ApiKeyCreateResponse(api_key=read_api_key(api_key), secret=signing_secret)

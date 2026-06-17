from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import ApiMessage, CurrentUser, Page
from bitnp_ideas.security.rbac import require_roles
from bitnp_ideas.services.backend import (
    add_audit,
    ensure_user_can_manage_user,
    normalized_limit,
    normalized_offset,
    total_for_statement,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SuperuserDep = Annotated[CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER))]
UserAdminDep = Annotated[
    CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR))
]


@router.get("", response_model=Page[CurrentUser])
async def list_users(
    _: UserAdminDep, session: DbSessionDep, offset: int = 0, limit: int = 50
) -> Page[CurrentUser]:
    statement = select(User).order_by(User.display_name)
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement.offset(normalized_offset(offset)).limit(normalized_limit(limit))
    )
    return Page(data=[CurrentUser.model_validate(user) for user in result], total=total)


@router.get("/{user_id}", response_model=CurrentUser)
async def get_user(user_id: str, _: UserAdminDep, session: DbSessionDep) -> CurrentUser:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return CurrentUser.model_validate(user)


@router.patch("/{user_id}/role", response_model=ApiMessage)
async def update_role(
    user_id: str,
    role: GlobalRole,
    actor: SuperuserDep,
    session: DbSessionDep,
) -> ApiMessage:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.global_role == GlobalRole.SUPERUSER and user.id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another superuser.",
        )

    before = {"global_role": user.global_role}
    user.global_role = role
    user.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="user.role_changed",
        entity_type="user",
        entity_id=user.id,
        before=before,
        after={"global_role": role},
    )
    await session.commit()
    return ApiMessage(message=f"user {user_id} role updated to {role}")


@router.patch("/{user_id}/active", response_model=ApiMessage)
async def update_active(
    user_id: str,
    is_active: bool,
    actor: UserAdminDep,
    session: DbSessionDep,
) -> ApiMessage:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    ensure_user_can_manage_user(actor, user)
    before = {"is_active": user.is_active}
    user.is_active = is_active
    user.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="user.active_changed",
        entity_type="user",
        entity_id=user.id,
        before=before,
        after={"is_active": is_active},
    )
    await session.commit()
    return ApiMessage(message=f"user {user_id} active={is_active}")

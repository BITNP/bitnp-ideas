from typing import Annotated

from fastapi import APIRouter, Depends

from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import ApiMessage, CurrentUser
from bitnp_ideas.security.rbac import require_roles
from bitnp_ideas.services import demo_data

router = APIRouter()
SuperuserDep = Annotated[CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER))]
UserAdminDep = Annotated[
    CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR))
]


@router.get("", response_model=list[CurrentUser])
async def list_users() -> list[CurrentUser]:
    return [demo_data.current_user]


@router.get("/{user_id}", response_model=CurrentUser)
async def get_user(user_id: str) -> CurrentUser:
    user = demo_data.current_user.model_copy()
    user.id = user_id
    return user


@router.patch("/{user_id}/role", response_model=ApiMessage)
async def update_role(
    user_id: str,
    role: GlobalRole,
    _: SuperuserDep,
) -> ApiMessage:
    return ApiMessage(message=f"user {user_id} role update scheduled: {role}")


@router.patch("/{user_id}/active", response_model=ApiMessage)
async def update_active(
    user_id: str,
    is_active: bool,
    _: UserAdminDep,
) -> ApiMessage:
    return ApiMessage(message=f"user {user_id} active={is_active}")

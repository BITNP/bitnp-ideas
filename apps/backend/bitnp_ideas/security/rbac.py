from typing import Annotated

from fastapi import Depends, HTTPException, status

from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import CurrentUser
from bitnp_ideas.services import demo_data


async def get_current_user() -> CurrentUser:
    return demo_data.current_user


def require_roles(*roles: GlobalRole):
    async def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.global_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient global role for this operation.",
            )
        return user

    return dependency

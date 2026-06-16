from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ActivityStream
from bitnp_ideas.schemas.common import ActivityRead, CurrentUser
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import ensure_project_access, serialize_activity

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/projects/{project_id}/activity", response_model=list[ActivityRead])
async def list_project_activity(
    project_id: str,
    user: CurrentUserDep,
    session: DbSessionDep,
    actor_user_id: str | None = None,
    action_type: str | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[ActivityRead]:
    await ensure_project_access(session, user, project_id)
    statement = (
        select(ActivityStream)
        .where(ActivityStream.project_id == project_id)
        .order_by(ActivityStream.created_at.desc(), ActivityStream.id.desc())
        .limit(min(limit, 100))
    )
    if actor_user_id:
        statement = statement.where(ActivityStream.actor_user_id == actor_user_id)
    if action_type:
        statement = statement.where(ActivityStream.action_type == action_type)
    if entity_type:
        statement = statement.where(ActivityStream.entity_type == entity_type)
    if cursor:
        statement = statement.where(ActivityStream.id < cursor)
    result = await session.scalars(statement)
    return [await serialize_activity(session, activity) for activity in result]

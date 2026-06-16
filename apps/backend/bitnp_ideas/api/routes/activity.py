from fastapi import APIRouter

from bitnp_ideas.schemas.common import ActivityRead
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("/projects/{project_id}/activity", response_model=list[ActivityRead])
async def list_project_activity(
    project_id: str,
    actor_user_id: str | None = None,
    action_type: str | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[ActivityRead]:
    _ = cursor
    results = [activity for activity in demo_data.activities if activity.project_id == project_id]
    if actor_user_id:
        results = [
            activity
            for activity in results
            if activity.actor and activity.actor.id == actor_user_id
        ]
    if action_type:
        results = [activity for activity in results if activity.action_type == action_type]
    if entity_type:
        results = [activity for activity in results if activity.entity_type == entity_type]
    return results[:limit]

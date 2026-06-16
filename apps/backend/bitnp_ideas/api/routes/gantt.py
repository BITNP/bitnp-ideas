from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiMessage, GanttBulkUpdate, GanttRead
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("/projects/{project_id}/gantt", response_model=GanttRead)
async def get_gantt(project_id: str) -> GanttRead:
    return demo_data.gantt.model_copy(
        update={"project": demo_data.projects[0].model_copy(update={"id": project_id})}
    )


@router.patch("/projects/{project_id}/gantt/bulk", response_model=ApiMessage)
async def bulk_update_gantt(project_id: str, payload: GanttBulkUpdate) -> ApiMessage:
    return ApiMessage(
        message=f"{len(payload.changes)} gantt changes accepted for project {project_id}"
    )


@router.post("/projects/{project_id}/task-dependencies", response_model=ApiMessage)
async def create_dependency(
    project_id: str,
    predecessor_task_id: str,
    successor_task_id: str,
    dependency_type: str = "finish_to_start",
) -> ApiMessage:
    return ApiMessage(
        message=(
            f"dependency {predecessor_task_id}->{successor_task_id} "
            f"({dependency_type}) queued for project {project_id}"
        )
    )


@router.delete(
    "/projects/{project_id}/task-dependencies/{dependency_id}", response_model=ApiMessage
)
async def delete_dependency(project_id: str, dependency_id: str) -> ApiMessage:
    return ApiMessage(message=f"dependency {dependency_id} deleted from project {project_id}")

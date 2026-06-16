from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiMessage, TaskCreate, TaskRead
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_project_tasks(project_id: str) -> list[TaskRead]:
    return [task for task in demo_data.tasks if task.project_id == project_id]


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
async def create_project_task(project_id: str, payload: TaskCreate) -> TaskRead:
    return demo_data.tasks[0].model_copy(
        update={
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
        }
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: str) -> TaskRead:
    return next((task for task in demo_data.tasks if task.id == task_id), demo_data.tasks[0])


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: str, payload: TaskCreate) -> TaskRead:
    task = await get_task(task_id)
    return task.model_copy(update=payload.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", response_model=ApiMessage)
async def archive_task(task_id: str) -> ApiMessage:
    return ApiMessage(message=f"task {task_id} archived")

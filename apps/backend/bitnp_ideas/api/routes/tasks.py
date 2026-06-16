from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ProjectTask
from bitnp_ideas.models.enums import TaskStatus
from bitnp_ideas.schemas.common import ApiMessage, CurrentUser, TaskCreate, TaskRead, TaskUpdate
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import (
    add_activity,
    add_audit,
    ensure_project_access,
    ensure_project_member,
    serialize_task,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def validate_task_dates(start_date, end_date) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task start_date cannot be after end_date.",
        )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_project_tasks(
    project_id: str,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> list[TaskRead]:
    await ensure_project_access(session, user, project_id)
    result = await session.scalars(
        select(ProjectTask)
        .where(ProjectTask.project_id == project_id, ProjectTask.archived_at.is_(None))
        .order_by(ProjectTask.sort_order, ProjectTask.created_at)
    )
    return [await serialize_task(session, task) for task in result]


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
async def create_project_task(
    project_id: str,
    payload: TaskCreate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> TaskRead:
    await ensure_project_access(session, user, project_id, write=True)
    await ensure_project_member(session, project_id, payload.assignee_id)
    validate_task_dates(payload.start_date, payload.end_date)
    task = ProjectTask(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=TaskStatus.TODO,
        assignee_id=payload.assignee_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_by=user.id,
    )
    session.add(task)
    await session.flush()
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=user.id,
        action_type="task.created",
        entity_type="task",
        entity_id=task.id,
        after={"title": task.title},
    )
    add_audit(
        session,
        actor_user_id=user.id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        after={"project_id": project_id, "title": task.title},
    )
    await session.commit()
    await session.refresh(task)
    return await serialize_task(session, task)


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: str, user: CurrentUserDep, session: DbSessionDep) -> TaskRead:
    task = await session.get(ProjectTask, task_id)
    if task is None or task.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    await ensure_project_access(session, user, task.project_id)
    return await serialize_task(session, task)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> TaskRead:
    task = await session.get(ProjectTask, task_id)
    if task is None or task.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    await ensure_project_access(session, user, task.project_id, write=True)
    if payload.version is not None and payload.version != task.version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task version conflict.")
    await ensure_project_member(session, task.project_id, payload.assignee_id)
    next_start = payload.start_date if payload.start_date is not None else task.start_date
    next_end = payload.end_date if payload.end_date is not None else task.end_date
    validate_task_dates(next_start, next_end)
    before = {
        "title": task.title,
        "status": task.status,
        "assignee_id": task.assignee_id,
        "start_date": str(task.start_date) if task.start_date else None,
        "end_date": str(task.end_date) if task.end_date else None,
        "progress": task.progress,
        "version": task.version,
    }
    updates = payload.model_dump(exclude_unset=True, exclude={"version"})
    for field, value in updates.items():
        setattr(task, field, value)
    task.version += 1
    task.updated_at = utcnow()
    add_activity(
        session,
        project_id=task.project_id,
        actor_user_id=user.id,
        action_type="task.updated",
        entity_type="task",
        entity_id=task.id,
        before=before,
        after=updates | {"version": task.version},
    )
    add_audit(
        session,
        actor_user_id=user.id,
        action="task.updated",
        entity_type="task",
        entity_id=task.id,
        before=before,
        after=updates | {"version": task.version},
    )
    await session.commit()
    await session.refresh(task)
    return await serialize_task(session, task)


@router.delete("/tasks/{task_id}", response_model=ApiMessage)
async def archive_task(task_id: str, user: CurrentUserDep, session: DbSessionDep) -> ApiMessage:
    task = await session.get(ProjectTask, task_id)
    if task is None or task.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    await ensure_project_access(session, user, task.project_id, write=True)
    task.archived_at = utcnow()
    task.updated_at = utcnow()
    add_activity(
        session,
        project_id=task.project_id,
        actor_user_id=user.id,
        action_type="task.archived",
        entity_type="task",
        entity_id=task.id,
    )
    add_audit(
        session,
        actor_user_id=user.id,
        action="task.archived",
        entity_type="task",
        entity_id=task.id,
    )
    await session.commit()
    return ApiMessage(message=f"task {task_id} archived")

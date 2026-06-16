from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import Project, ProjectTask, TaskDependency
from bitnp_ideas.schemas.common import (
    ApiMessage,
    CurrentUser,
    GanttBulkUpdate,
    GanttDependency,
    GanttRead,
    TaskDependencyCreate,
)
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import (
    add_activity,
    add_audit,
    ensure_project_access,
    ensure_project_member,
    serialize_project,
    serialize_task,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


async def project_dependencies(session: AsyncSession, project_id: str) -> list[TaskDependency]:
    result = await session.scalars(
        select(TaskDependency).where(TaskDependency.project_id == project_id)
    )
    return list(result)


def creates_cycle(
    dependencies: list[TaskDependency],
    predecessor_task_id: str,
    successor_task_id: str,
) -> bool:
    graph: dict[str, list[str]] = {}
    for dependency in dependencies:
        graph.setdefault(dependency.predecessor_task_id, []).append(dependency.successor_task_id)
    graph.setdefault(predecessor_task_id, []).append(successor_task_id)

    stack = [successor_task_id]
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current == predecessor_task_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(graph.get(current, []))
    return False


@router.get("/projects/{project_id}/gantt", response_model=GanttRead)
async def get_gantt(project_id: str, user: CurrentUserDep, session: DbSessionDep) -> GanttRead:
    await ensure_project_access(session, user, project_id)
    project = await session.get(Project, project_id)
    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    task_result = await session.scalars(
        select(ProjectTask)
        .where(ProjectTask.project_id == project_id, ProjectTask.archived_at.is_(None))
        .order_by(ProjectTask.sort_order, ProjectTask.created_at)
    )
    dependencies = await project_dependencies(session, project_id)
    return GanttRead(
        project=await serialize_project(session, project),
        tasks=[await serialize_task(session, task) for task in task_result],
        dependencies=[
            GanttDependency(
                id=dependency.id,
                predecessor_task_id=dependency.predecessor_task_id,
                successor_task_id=dependency.successor_task_id,
                dependency_type=dependency.dependency_type,
            )
            for dependency in dependencies
        ],
    )


@router.patch("/projects/{project_id}/gantt/bulk", response_model=ApiMessage)
async def bulk_update_gantt(
    project_id: str,
    payload: GanttBulkUpdate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiMessage:
    await ensure_project_access(session, user, project_id, write=True)
    for change in payload.changes:
        task = await session.get(ProjectTask, change.task_id)
        if task is None or task.project_id != project_id or task.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if change.version != task.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Task version conflict."
            )
        await ensure_project_member(session, project_id, change.assignee_id)
        next_start = change.start_date if change.start_date is not None else task.start_date
        next_end = change.end_date if change.end_date is not None else task.end_date
        if next_start and next_end and next_start > next_end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task start_date cannot be after end_date.",
            )
        before = {
            "start_date": str(task.start_date) if task.start_date else None,
            "end_date": str(task.end_date) if task.end_date else None,
            "assignee_id": task.assignee_id,
            "progress": task.progress,
            "version": task.version,
        }
        updates = change.model_dump(exclude_unset=True, exclude={"task_id", "version"})
        for field, value in updates.items():
            setattr(task, field, value)
        task.version += 1
        task.updated_at = utcnow()
        add_activity(
            session,
            project_id=project_id,
            actor_user_id=user.id,
            action_type="task.rescheduled",
            entity_type="task",
            entity_id=task.id,
            before=before,
            after=updates | {"version": task.version},
        )
        add_audit(
            session,
            actor_user_id=user.id,
            action="gantt.task_updated",
            entity_type="task",
            entity_id=task.id,
            before=before,
            after=updates | {"version": task.version},
        )
    await session.commit()
    return ApiMessage(
        message=f"{len(payload.changes)} gantt changes accepted for project {project_id}"
    )


@router.post("/projects/{project_id}/task-dependencies", response_model=ApiMessage)
async def create_dependency(
    project_id: str,
    payload: TaskDependencyCreate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiMessage:
    await ensure_project_access(session, user, project_id, write=True)
    if payload.predecessor_task_id == payload.successor_task_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency cannot target itself.",
        )
    predecessor = await session.get(ProjectTask, payload.predecessor_task_id)
    successor = await session.get(ProjectTask, payload.successor_task_id)
    if predecessor is None or successor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if predecessor.project_id != project_id or successor.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task dependencies cannot cross projects.",
        )
    dependencies = await project_dependencies(session, project_id)
    if creates_cycle(dependencies, payload.predecessor_task_id, payload.successor_task_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Dependency creates a cycle."
        )
    exists = await session.scalar(
        select(TaskDependency).where(
            TaskDependency.predecessor_task_id == payload.predecessor_task_id,
            TaskDependency.successor_task_id == payload.successor_task_id,
        )
    )
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Dependency already exists."
        )
    dependency = TaskDependency(
        project_id=project_id,
        predecessor_task_id=payload.predecessor_task_id,
        successor_task_id=payload.successor_task_id,
        dependency_type=payload.dependency_type,
        created_by=user.id,
        created_at=utcnow(),
    )
    session.add(dependency)
    await session.flush()
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=user.id,
        action_type="task.dependency_created",
        entity_type="task_dependency",
        entity_id=dependency.id,
        after=payload.model_dump(),
    )
    add_audit(
        session,
        actor_user_id=user.id,
        action="task.dependency_created",
        entity_type="task_dependency",
        entity_id=dependency.id,
        after=payload.model_dump(),
    )
    await session.commit()
    return ApiMessage(message=f"dependency {dependency.id} created for project {project_id}")


@router.delete(
    "/projects/{project_id}/task-dependencies/{dependency_id}", response_model=ApiMessage
)
async def delete_dependency(
    project_id: str,
    dependency_id: str,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ApiMessage:
    await ensure_project_access(session, user, project_id, write=True)
    dependency = await session.get(TaskDependency, dependency_id)
    if dependency is None or dependency.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found.")
    before = {
        "predecessor_task_id": dependency.predecessor_task_id,
        "successor_task_id": dependency.successor_task_id,
    }
    await session.delete(dependency)
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=user.id,
        action_type="task.dependency_deleted",
        entity_type="task_dependency",
        entity_id=dependency_id,
        before=before,
    )
    add_audit(
        session,
        actor_user_id=user.id,
        action="task.dependency_deleted",
        entity_type="task_dependency",
        entity_id=dependency_id,
        before=before,
    )
    await session.commit()
    return ApiMessage(message=f"dependency {dependency_id} deleted from project {project_id}")

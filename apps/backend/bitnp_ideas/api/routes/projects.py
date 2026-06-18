from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import Idea, Project, ProjectIdea, ProjectMember, User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import (
    ApiMessage,
    CurrentUser,
    IdeaRead,
    Page,
    ProjectCreate,
    ProjectIdeaLinkCreate,
    ProjectMemberCreate,
    ProjectRead,
    ProjectUpdate,
)
from bitnp_ideas.security.rbac import get_current_user, require_roles
from bitnp_ideas.services.backend import (
    add_activity,
    add_audit,
    ensure_project_access,
    normalized_limit,
    normalized_offset,
    serialize_idea,
    serialize_project,
    total_for_statement,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ProjectAdminDep = Annotated[
    CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR))
]


@router.get("", response_model=Page[ProjectRead])
async def list_projects(
    user: CurrentUserDep, session: DbSessionDep, offset: int = 0, limit: int = 50
) -> Page[ProjectRead]:
    statement = (
        select(Project).where(Project.archived_at.is_(None)).order_by(Project.updated_at.desc())
    )
    if user.global_role == GlobalRole.DEVELOPER:
        statement = statement.join(ProjectMember).where(ProjectMember.user_id == user.id)
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement.offset(normalized_offset(offset)).limit(normalized_limit(limit))
    )
    return Page(data=[await serialize_project(session, project) for project in result], total=total)


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ProjectRead:
    if payload.owner_id and await session.get(User, payload.owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.")
    project = Project(
        key=payload.key.upper(),
        name=payload.name,
        description=payload.description,
        status="planning",
        owner_id=payload.owner_id,
        created_by=actor.id,
    )
    session.add(project)
    await session.flush()
    session.add(
        ProjectMember(
            project_id=project.id, user_id=actor.id, added_by=actor.id, created_at=utcnow()
        )
    )
    if payload.owner_id and payload.owner_id != actor.id:
        session.add(
            ProjectMember(
                project_id=project.id,
                user_id=payload.owner_id,
                added_by=actor.id,
                created_at=utcnow(),
            )
        )
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.created",
        entity_type="project",
        entity_id=project.id,
        after={"key": project.key, "name": project.name},
    )
    await session.commit()
    await session.refresh(project)
    return await serialize_project(session, project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, user: CurrentUserDep, session: DbSessionDep) -> ProjectRead:
    await ensure_project_access(session, user, project_id)
    project = await session.get(Project, project_id)
    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return await serialize_project(session, project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ProjectRead:
    project = await session.get(Project, project_id)
    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    before = {
        "key": project.key,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "owner_id": project.owner_id,
    }
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(
            project, field, value.upper() if field == "key" and isinstance(value, str) else value
        )
    project.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.updated",
        entity_type="project",
        entity_id=project.id,
        before=before,
        after=updates,
    )
    await session.commit()
    await session.refresh(project)
    return await serialize_project(session, project)


@router.delete("/{project_id}", response_model=ApiMessage)
async def archive_project(
    project_id: str, actor: ProjectAdminDep, session: DbSessionDep
) -> ApiMessage:
    project = await session.get(Project, project_id)
    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    project.archived_at = utcnow()
    project.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.archived",
        entity_type="project",
        entity_id=project.id,
    )
    await session.commit()
    return ApiMessage(message=f"project {project_id} archived")


@router.post("/{project_id}/members", response_model=ApiMessage)
async def add_project_member(
    project_id: str,
    payload: ProjectMemberCreate,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ApiMessage:
    if await session.get(Project, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if await session.get(User, payload.user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    exists = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
    )
    if exists is None:
        session.add(
            ProjectMember(
                project_id=project_id,
                user_id=payload.user_id,
                added_by=actor.id,
                created_at=utcnow(),
            )
        )
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=actor.id,
        action_type="project.member_added",
        entity_type="user",
        entity_id=payload.user_id,
    )
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.member_added",
        entity_type="project",
        entity_id=project_id,
        after={"user_id": payload.user_id},
    )
    await session.commit()
    return ApiMessage(message=f"user {payload.user_id} added to project {project_id}")


@router.delete("/{project_id}/members/{user_id}", response_model=ApiMessage)
async def remove_project_member(
    project_id: str,
    user_id: str,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ApiMessage:
    member = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found."
        )
    await session.delete(member)
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=actor.id,
        action_type="project.member_removed",
        entity_type="user",
        entity_id=user_id,
    )
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.member_removed",
        entity_type="project",
        entity_id=project_id,
        before={"user_id": user_id},
    )
    await session.commit()
    return ApiMessage(message=f"user {user_id} removed from project {project_id}")


@router.get("/{project_id}/ideas", response_model=Page[IdeaRead])
async def list_project_ideas(
    project_id: str,
    user: CurrentUserDep,
    session: DbSessionDep,
    offset: int = 0,
    limit: int = 50,
) -> Page[IdeaRead]:
    await ensure_project_access(session, user, project_id)
    statement = (
        select(Idea)
        .join(ProjectIdea, ProjectIdea.idea_id == Idea.id)
        .where(ProjectIdea.project_id == project_id)
        .order_by(Idea.updated_at.desc())
    )
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement
        .offset(normalized_offset(offset))
        .limit(normalized_limit(limit))
    )
    return Page(data=[await serialize_idea(session, idea) for idea in result], total=total)


@router.post("/{project_id}/ideas", response_model=ApiMessage)
async def link_project_idea(
    project_id: str,
    payload: ProjectIdeaLinkCreate,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ApiMessage:
    if await session.get(Project, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if await session.get(Idea, payload.idea_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    exists = await session.scalar(
        select(ProjectIdea).where(
            ProjectIdea.project_id == project_id,
            ProjectIdea.idea_id == payload.idea_id,
        )
    )
    if exists is None:
        session.add(
            ProjectIdea(
                project_id=project_id,
                idea_id=payload.idea_id,
                relation_type=payload.relation_type,
                created_by=actor.id,
                created_at=utcnow(),
            )
        )
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=actor.id,
        action_type="idea.linked",
        entity_type="idea",
        entity_id=payload.idea_id,
    )
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.idea_linked",
        entity_type="project",
        entity_id=project_id,
        after={"idea_id": payload.idea_id, "relation_type": payload.relation_type},
    )
    await session.commit()
    return ApiMessage(message=f"idea {payload.idea_id} linked to project {project_id}")


@router.delete("/{project_id}/ideas/{idea_id}", response_model=ApiMessage)
async def unlink_project_idea(
    project_id: str,
    idea_id: str,
    actor: ProjectAdminDep,
    session: DbSessionDep,
) -> ApiMessage:
    link = await session.scalar(
        select(ProjectIdea).where(
            ProjectIdea.project_id == project_id, ProjectIdea.idea_id == idea_id
        )
    )
    if link is not None:
        await session.delete(link)
    add_activity(
        session,
        project_id=project_id,
        actor_user_id=actor.id,
        action_type="idea.unlinked",
        entity_type="idea",
        entity_id=idea_id,
    )
    add_audit(
        session,
        actor_user_id=actor.id,
        action="project.idea_unlinked",
        entity_type="project",
        entity_id=project_id,
        before={"idea_id": idea_id},
    )
    await session.commit()
    return ApiMessage(message=f"idea {idea_id} unlinked from project {project_id}")

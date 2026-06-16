import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.models.entities import (
    ActivityStream,
    AuditLog,
    Idea,
    IdeaTag,
    IdeaTagLink,
    Project,
    ProjectMember,
    ProjectTask,
    User,
)
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import (
    ActivityRead,
    CurrentUser,
    EntityRef,
    IdeaRead,
    IdeaTagRead,
    ProjectRead,
    TaskRead,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "tag"


def entity_ref(user_or_project: User | Project | None) -> EntityRef | None:
    if user_or_project is None:
        return None
    name = getattr(user_or_project, "display_name", None) or user_or_project.name
    return EntityRef(id=user_or_project.id, name=name)


def ensure_user_can_manage_user(actor: CurrentUser, target: User) -> None:
    if actor.global_role == GlobalRole.SUPERUSER:
        return
    if target.global_role == GlobalRole.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot modify superusers.",
        )
    if actor.global_role != GlobalRole.ADMINISTRATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")


async def ensure_project_access(
    session: AsyncSession,
    user: CurrentUser,
    project_id: str,
    write: bool = False,
) -> None:
    if user.global_role in {GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR}:
        return
    member = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied.")
    if write and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive users cannot write."
        )


async def ensure_project_member(
    session: AsyncSession, project_id: str, user_id: str | None
) -> None:
    if user_id is None:
        return
    member = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignee must be a project member.",
        )


async def idea_tags(session: AsyncSession, idea_id: str) -> list[IdeaTagRead]:
    result = await session.execute(
        select(IdeaTag, func.count(IdeaTagLink.idea_id))
        .join(IdeaTagLink, IdeaTagLink.tag_id == IdeaTag.id)
        .where(IdeaTagLink.idea_id == idea_id)
        .group_by(IdeaTag.id)
        .order_by(IdeaTag.name)
    )
    return [
        IdeaTagRead.model_validate(tag).model_copy(update={"usage_count": usage_count})
        for tag, usage_count in result.all()
    ]


async def serialize_tag(session: AsyncSession, tag: IdeaTag) -> IdeaTagRead:
    usage_count = await session.scalar(
        select(func.count()).select_from(IdeaTagLink).where(IdeaTagLink.tag_id == tag.id)
    )
    return IdeaTagRead.model_validate(tag).model_copy(update={"usage_count": usage_count or 0})


async def serialize_idea(session: AsyncSession, idea: Idea) -> IdeaRead:
    creator = await session.get(User, idea.creator_id)
    linked_project = (
        await session.get(Project, idea.linked_project_id) if idea.linked_project_id else None
    )
    return IdeaRead(
        id=idea.id,
        title=idea.title,
        description=idea.description,
        status=idea.status,
        priority=idea.priority,
        tags=await idea_tags(session, idea.id),
        creator=entity_ref(creator) or EntityRef(id=idea.creator_id, name="Unknown"),
        linked_project=entity_ref(linked_project),
        linked_project_url=idea.linked_project_url,
        created_at=idea.created_at,
        updated_at=idea.updated_at,
    )


async def serialize_project(session: AsyncSession, project: Project) -> ProjectRead:
    owner = await session.get(User, project.owner_id) if project.owner_id else None
    members_result = await session.scalars(
        select(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project.id)
        .order_by(User.display_name)
    )
    tasks = await session.scalars(
        select(ProjectTask).where(
            ProjectTask.project_id == project.id,
            ProjectTask.archived_at.is_(None),
        )
    )
    task_list = list(tasks)
    progress = round(sum(task.progress for task in task_list) / len(task_list)) if task_list else 0
    return ProjectRead(
        id=project.id,
        key=project.key,
        name=project.name,
        description=project.description,
        status=project.status,
        owner=entity_ref(owner),
        progress=progress,
        start_date=project.start_date,
        target_end_date=project.target_end_date,
        members=[EntityRef(id=user.id, name=user.display_name) for user in members_result],
    )


async def serialize_task(session: AsyncSession, task: ProjectTask) -> TaskRead:
    assignee = await session.get(User, task.assignee_id) if task.assignee_id else None
    return TaskRead(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        assignee=entity_ref(assignee),
        start_date=task.start_date,
        end_date=task.end_date,
        progress=task.progress,
        version=task.version,
    )


async def serialize_activity(session: AsyncSession, activity: ActivityStream) -> ActivityRead:
    actor = await session.get(User, activity.actor_user_id) if activity.actor_user_id else None
    return ActivityRead(
        id=activity.id,
        project_id=activity.project_id,
        actor=entity_ref(actor),
        action_type=activity.action_type,
        entity_type=activity.entity_type,
        entity_id=activity.entity_id,
        before=activity.before,
        after=activity.after,
        created_at=activity.created_at,
    )


def add_audit(
    session: AsyncSession,
    *,
    actor_user_id: str | None,
    actor_api_key_id: str | None = None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            actor_api_key_id=actor_api_key_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            metadata_=metadata,
            created_at=utcnow(),
        )
    )


def add_activity(
    session: AsyncSession,
    *,
    project_id: str,
    actor_user_id: str | None,
    action_type: str,
    entity_type: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
) -> None:
    session.add(
        ActivityStream(
            project_id=project_id,
            actor_user_id=actor_user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            metadata_=metadata,
            created_at=utcnow(),
        )
    )

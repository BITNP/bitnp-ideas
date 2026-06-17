from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import Idea, IdeaStatusHistory, IdeaTag, IdeaTagLink
from bitnp_ideas.models.enums import GlobalRole, IdeaStatus
from bitnp_ideas.schemas.common import (
    ApiMessage,
    IdeaCreate,
    IdeaRead,
    IdeaStatusHistoryRead,
    IdeaStatusUpdate,
    IdeaTagAttach,
    IdeaUpdate,
    Page,
)
from bitnp_ideas.security.api_keys import scope_allowed
from bitnp_ideas.security.rbac import AuthContext, get_auth_context
from bitnp_ideas.services.backend import (
    add_audit,
    normalized_limit,
    normalized_offset,
    serialize_idea,
    total_for_statement,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
AuthDep = Annotated[AuthContext, Depends(get_auth_context)]


def ensure_idea_read(context: AuthContext) -> None:
    if context.api_key and not scope_allowed(context.api_key, "ideas:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key lacks ideas:read."
        )


def ensure_idea_write(context: AuthContext) -> None:
    if context.api_key and not scope_allowed(context.api_key, "ideas:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key lacks ideas:write."
        )


def ensure_idea_owner_or_admin(context: AuthContext, idea: Idea) -> None:
    if context.user.global_role in {GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR}:
        return
    if idea.creator_id != context.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Idea access denied.")


async def existing_tags_by_names(session: AsyncSession, tag_names: list[str]) -> list[IdeaTag]:
    if not tag_names:
        return []
    normalized = {name.strip().lower() for name in tag_names if name.strip()}
    if not normalized:
        return []
    result = await session.scalars(select(IdeaTag).where(IdeaTag.name.in_(normalized)))
    tags = list(result)
    if len(tags) != len(normalized):
        missing = normalized - {tag.name for tag in tags}
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown tags: {', '.join(sorted(missing))}",
        )
    return tags


def validate_status_link(
    status_value: IdeaStatus,
    linked_project_id: str | None,
    linked_project_url: str | None,
) -> None:
    if status_value in {IdeaStatus.IN_PROGRESS, IdeaStatus.COMPLETED} and not (
        linked_project_id or linked_project_url
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="in_progress/completed ideas must link to a project or URL.",
        )


@router.get("", response_model=Page[IdeaRead])
async def list_ideas(
    context: AuthDep,
    session: DbSessionDep,
    status: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> Page[IdeaRead]:
    ensure_idea_read(context)
    statement = select(Idea).where(Idea.archived_at.is_(None)).order_by(Idea.updated_at.desc())
    if status:
        statement = statement.where(Idea.status == status)
    if tag:
        statement = statement.where(Idea.tags.any(IdeaTag.slug == tag))
    if search:
        statement = statement.where(Idea.title.ilike(f"%{search}%"))
    total = await total_for_statement(session, statement)
    results = await session.scalars(
        statement.offset(normalized_offset(offset)).limit(normalized_limit(limit))
    )
    return Page(data=[await serialize_idea(session, idea) for idea in results], total=total)


@router.post("", response_model=IdeaRead, status_code=201)
async def create_idea(payload: IdeaCreate, context: AuthDep, session: DbSessionDep) -> IdeaRead:
    ensure_idea_write(context)
    tags = await existing_tags_by_names(session, payload.tag_names)
    idea = Idea(
        title=payload.title,
        description=payload.description,
        status=IdeaStatus.ACTIVE,
        creator_id=context.user.id,
        priority=payload.priority,
    )
    session.add(idea)
    await session.flush()
    now = utcnow()
    for tag in tags:
        session.add(
            IdeaTagLink(idea_id=idea.id, tag_id=tag.id, added_by=context.user.id, created_at=now)
        )
    session.add(
        IdeaStatusHistory(
            idea_id=idea.id,
            from_status=None,
            to_status=IdeaStatus.ACTIVE,
            actor_id=context.user.id,
            created_at=now,
        )
    )
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.created",
        entity_type="idea",
        entity_id=idea.id,
        after={"title": idea.title, "status": idea.status},
    )
    await session.commit()
    await session.refresh(idea)
    return await serialize_idea(session, idea)


@router.get("/{idea_id}", response_model=IdeaRead)
async def get_idea(idea_id: str, context: AuthDep, session: DbSessionDep) -> IdeaRead:
    ensure_idea_read(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    return await serialize_idea(session, idea)


@router.patch("/{idea_id}", response_model=IdeaRead)
async def update_idea(
    idea_id: str, payload: IdeaUpdate, context: AuthDep, session: DbSessionDep
) -> IdeaRead:
    ensure_idea_write(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    ensure_idea_owner_or_admin(context, idea)
    before = {
        "title": idea.title,
        "description": idea.description,
        "priority": idea.priority,
        "linked_project_id": idea.linked_project_id,
        "linked_project_url": idea.linked_project_url,
    }
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(idea, field, value)
    validate_status_link(idea.status, idea.linked_project_id, idea.linked_project_url)
    idea.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.updated",
        entity_type="idea",
        entity_id=idea.id,
        before=before,
        after=updates,
    )
    await session.commit()
    await session.refresh(idea)
    return await serialize_idea(session, idea)


@router.delete("/{idea_id}", response_model=ApiMessage)
async def archive_idea(idea_id: str, context: AuthDep, session: DbSessionDep) -> ApiMessage:
    ensure_idea_write(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    ensure_idea_owner_or_admin(context, idea)
    idea.archived_at = datetime.now(UTC)
    idea.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.archived",
        entity_type="idea",
        entity_id=idea.id,
    )
    await session.commit()
    return ApiMessage(message=f"idea {idea_id} archived")


@router.post("/{idea_id}/status", response_model=ApiMessage)
async def update_idea_status(
    idea_id: str,
    payload: IdeaStatusUpdate,
    context: AuthDep,
    session: DbSessionDep,
) -> ApiMessage:
    ensure_idea_write(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    ensure_idea_owner_or_admin(context, idea)
    linked_project_id = payload.linked_project_id or idea.linked_project_id
    linked_project_url = payload.linked_project_url or idea.linked_project_url
    validate_status_link(payload.status, linked_project_id, linked_project_url)

    before = {
        "status": idea.status,
        "linked_project_id": idea.linked_project_id,
        "linked_project_url": idea.linked_project_url,
    }
    old_status = idea.status
    idea.status = payload.status
    idea.linked_project_id = linked_project_id
    idea.linked_project_url = linked_project_url
    idea.updated_at = utcnow()
    session.add(
        IdeaStatusHistory(
            idea_id=idea.id,
            from_status=old_status,
            to_status=payload.status,
            actor_id=context.user.id,
            note=payload.note,
            linked_project_id=linked_project_id,
            linked_project_url=linked_project_url,
            created_at=utcnow(),
        )
    )
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.status_changed",
        entity_type="idea",
        entity_id=idea.id,
        before=before,
        after={
            "status": payload.status,
            "linked_project_id": linked_project_id,
            "linked_project_url": linked_project_url,
        },
    )
    await session.commit()
    return ApiMessage(message=f"idea {idea_id} status changed to {payload.status}")


@router.get("/{idea_id}/history", response_model=Page[IdeaStatusHistoryRead])
async def get_idea_history(
    idea_id: str,
    context: AuthDep,
    session: DbSessionDep,
    offset: int = 0,
    limit: int = 50,
) -> Page[IdeaStatusHistoryRead]:
    ensure_idea_read(context)
    statement = (
        select(IdeaStatusHistory)
        .where(IdeaStatusHistory.idea_id == idea_id)
        .order_by(IdeaStatusHistory.created_at.desc())
    )
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement
        .offset(normalized_offset(offset))
        .limit(normalized_limit(limit))
    )
    return Page(data=[IdeaStatusHistoryRead.model_validate(item) for item in result], total=total)


@router.post("/{idea_id}/tags", response_model=ApiMessage)
async def add_idea_tags(
    idea_id: str,
    payload: IdeaTagAttach,
    context: AuthDep,
    session: DbSessionDep,
) -> ApiMessage:
    ensure_idea_write(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    ensure_idea_owner_or_admin(context, idea)
    tags = await session.scalars(select(IdeaTag).where(IdeaTag.id.in_(payload.tag_ids)))
    tag_list = list(tags)
    if len(tag_list) != len(set(payload.tag_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown tag id."
        )
    now = utcnow()
    for tag in tag_list:
        exists = await session.get(IdeaTagLink, {"idea_id": idea_id, "tag_id": tag.id})
        if exists is None:
            session.add(
                IdeaTagLink(
                    idea_id=idea_id, tag_id=tag.id, added_by=context.user.id, created_at=now
                )
            )
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.tags_added",
        entity_type="idea",
        entity_id=idea_id,
        after={"tag_ids": payload.tag_ids},
    )
    await session.commit()
    return ApiMessage(message=f"added {len(tag_list)} tags to idea {idea_id}")


@router.delete("/{idea_id}/tags/{tag_id}", response_model=ApiMessage)
async def remove_idea_tag(
    idea_id: str,
    tag_id: str,
    context: AuthDep,
    session: DbSessionDep,
) -> ApiMessage:
    ensure_idea_write(context)
    idea = await session.get(Idea, idea_id)
    if idea is None or idea.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found.")
    ensure_idea_owner_or_admin(context, idea)
    link = await session.get(IdeaTagLink, {"idea_id": idea_id, "tag_id": tag_id})
    if link is not None:
        await session.delete(link)
    add_audit(
        session,
        actor_user_id=context.user.id,
        actor_api_key_id=context.api_key.id if context.api_key else None,
        action="idea.tag_removed",
        entity_type="idea",
        entity_id=idea_id,
        before={"tag_id": tag_id},
    )
    await session.commit()
    return ApiMessage(message=f"removed tag {tag_id} from idea {idea_id}")

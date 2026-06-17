from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import IdeaTag
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import (
    ApiMessage,
    CurrentUser,
    IdeaTagCreate,
    IdeaTagRead,
    IdeaTagUpdate,
    Page,
)
from bitnp_ideas.security.api_keys import scope_allowed
from bitnp_ideas.security.rbac import AuthContext, get_auth_context, require_roles
from bitnp_ideas.services.backend import (
    add_audit,
    normalized_limit,
    normalized_offset,
    serialize_tag,
    slugify,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
AuthDep = Annotated[AuthContext, Depends(get_auth_context)]
TagAdminDep = Annotated[
    CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR))
]


@router.get("", response_model=Page[IdeaTagRead])
async def list_tags(
    context: AuthDep, session: DbSessionDep, offset: int = 0, limit: int = 50
) -> Page[IdeaTagRead]:
    if context.api_key and not scope_allowed(context.api_key, "ideas:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key lacks ideas:read."
        )
    result = await session.scalars(select(IdeaTag).order_by(IdeaTag.name))
    tags = [await serialize_tag(session, tag) for tag in result]
    sorted_tags = sorted(tags, key=lambda item: (-item.usage_count, item.name))
    start = normalized_offset(offset)
    stop = start + normalized_limit(limit)
    return Page(data=sorted_tags[start:stop], total=len(sorted_tags))


@router.post("", response_model=IdeaTagRead, status_code=201)
async def create_tag(
    payload: IdeaTagCreate, actor: TagAdminDep, session: DbSessionDep
) -> IdeaTagRead:
    name = payload.name.strip().lower()
    tag = IdeaTag(
        name=name,
        slug=slugify(name),
        color=payload.color,
        description=payload.description,
        created_by=actor.id,
    )
    session.add(tag)
    await session.flush()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="idea_tag.created",
        entity_type="idea_tag",
        entity_id=tag.id,
        after={"name": tag.name, "slug": tag.slug},
    )
    await session.commit()
    await session.refresh(tag)
    return await serialize_tag(session, tag)


@router.get("/{tag_id}", response_model=IdeaTagRead)
async def get_tag(tag_id: str, context: AuthDep, session: DbSessionDep) -> IdeaTagRead:
    if context.api_key and not scope_allowed(context.api_key, "ideas:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key lacks ideas:read."
        )
    tag = await session.get(IdeaTag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return await serialize_tag(session, tag)


@router.patch("/{tag_id}", response_model=IdeaTagRead)
async def update_tag(
    tag_id: str,
    payload: IdeaTagUpdate,
    actor: TagAdminDep,
    session: DbSessionDep,
) -> IdeaTagRead:
    tag = await session.get(IdeaTag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    before = {
        "name": tag.name,
        "slug": tag.slug,
        "color": tag.color,
        "description": tag.description,
        "is_active": tag.is_active,
    }
    if payload.name is not None:
        tag.name = payload.name.strip().lower()
        tag.slug = slugify(tag.name)
    if payload.color is not None:
        tag.color = payload.color
    if payload.description is not None:
        tag.description = payload.description
    if payload.is_active is not None:
        tag.is_active = payload.is_active
    tag.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="idea_tag.updated",
        entity_type="idea_tag",
        entity_id=tag.id,
        before=before,
        after=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    await session.refresh(tag)
    return await serialize_tag(session, tag)


@router.delete("/{tag_id}", response_model=ApiMessage)
async def disable_tag(tag_id: str, actor: TagAdminDep, session: DbSessionDep) -> ApiMessage:
    tag = await session.get(IdeaTag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    before = {"is_active": tag.is_active}
    tag.is_active = False
    tag.updated_at = utcnow()
    add_audit(
        session,
        actor_user_id=actor.id,
        action="idea_tag.disabled",
        entity_type="idea_tag",
        entity_id=tag.id,
        before=before,
        after={"is_active": False},
    )
    await session.commit()
    return ApiMessage(message=f"tag {tag_id} disabled")

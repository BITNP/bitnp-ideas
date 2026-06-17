from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ExternalLink
from bitnp_ideas.models.enums import EntityType
from bitnp_ideas.schemas.common import (
    ApiMessage,
    CurrentUser,
    ExternalLinkCreate,
    ExternalLinkRead,
    LinkPreview,
    Page,
)
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import (
    add_audit,
    normalized_limit,
    normalized_offset,
    total_for_statement,
    utcnow,
)

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def parse_entity_type(entity_type: str) -> EntityType:
    try:
        return EntityType(entity_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="entity_type must be idea, project, or task.",
        ) from exc


def read_link(link: ExternalLink) -> ExternalLinkRead:
    return ExternalLinkRead(
        id=link.id,
        entity_type=link.entity_type,
        entity_id=link.entity_id,
        url=link.url,
        title=link.title,
        description=link.description,
        image_url=link.image_url,
        site_name=link.site_name,
        link_type=link.link_type,
        created_at=link.created_at,
    )


@router.get("/{entity_type}/{entity_id}/links", response_model=Page[ExternalLinkRead])
async def list_links(
    entity_type: str,
    entity_id: str,
    _: CurrentUserDep,
    session: DbSessionDep,
    offset: int = 0,
    limit: int = 50,
) -> Page[ExternalLinkRead]:
    parsed_type = parse_entity_type(entity_type)
    statement = (
        select(ExternalLink)
        .where(ExternalLink.entity_type == parsed_type, ExternalLink.entity_id == entity_id)
        .order_by(ExternalLink.created_at.desc())
    )
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement
        .offset(normalized_offset(offset))
        .limit(normalized_limit(limit))
    )
    return Page(data=[read_link(link) for link in result], total=total)


@router.post("/{entity_type}/{entity_id}/links", response_model=ExternalLinkRead, status_code=201)
async def create_link(
    entity_type: str,
    entity_id: str,
    payload: ExternalLinkCreate,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> ExternalLinkRead:
    parsed_type = parse_entity_type(entity_type)
    link = ExternalLink(
        entity_type=parsed_type,
        entity_id=entity_id,
        url=payload.url,
        title=payload.title,
        description=payload.description,
        link_type=payload.link_type,
        created_by=user.id,
        created_at=utcnow(),
    )
    session.add(link)
    await session.flush()
    add_audit(
        session,
        actor_user_id=user.id,
        action="external_link.created",
        entity_type=entity_type,
        entity_id=entity_id,
        after={"url": payload.url, "link_id": link.id},
    )
    await session.commit()
    await session.refresh(link)
    return read_link(link)


@router.delete("/links/{link_id}", response_model=ApiMessage)
async def delete_link(link_id: str, user: CurrentUserDep, session: DbSessionDep) -> ApiMessage:
    link = await session.get(ExternalLink, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")
    before = {"url": link.url, "link_id": link.id}
    entity_type = str(link.entity_type)
    entity_id = link.entity_id
    await session.delete(link)
    add_audit(
        session,
        actor_user_id=user.id,
        action="external_link.deleted",
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
    )
    await session.commit()
    return ApiMessage(message=f"link {link_id} deleted")


@router.post("/links/preview", response_model=LinkPreview)
async def preview_link(payload: ExternalLinkCreate) -> LinkPreview:
    return LinkPreview(
        url=payload.url,
        title=payload.title or payload.url,
        description=payload.description,
        image=None,
    )

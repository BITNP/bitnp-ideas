from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import ExternalLink
from bitnp_ideas.models.enums import EntityType
from bitnp_ideas.schemas.common import ApiMessage, CurrentUser, ExternalLinkCreate, ExternalLinkRead
from bitnp_ideas.security.rbac import get_current_user
from bitnp_ideas.services.backend import add_audit, utcnow

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
        link_type=link.link_type,
    )


@router.get("/{entity_type}/{entity_id}/links", response_model=list[ExternalLinkRead])
async def list_links(
    entity_type: str,
    entity_id: str,
    _: CurrentUserDep,
    session: DbSessionDep,
) -> list[ExternalLinkRead]:
    parsed_type = parse_entity_type(entity_type)
    result = await session.scalars(
        select(ExternalLink)
        .where(ExternalLink.entity_type == parsed_type, ExternalLink.entity_id == entity_id)
        .order_by(ExternalLink.created_at.desc())
    )
    return [read_link(link) for link in result]


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


@router.post("/links/preview", response_model=ExternalLinkRead)
async def preview_link(payload: ExternalLinkCreate) -> ExternalLinkRead:
    return ExternalLinkRead(
        id="preview",
        entity_type=EntityType.IDEA,
        entity_id="preview",
        url=payload.url,
        title=payload.title or payload.url,
        link_type=payload.link_type,
    )

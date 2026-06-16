from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiMessage, ExternalLinkCreate, ExternalLinkRead
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("/{entity_type}/{entity_id}/links", response_model=list[ExternalLinkRead])
async def list_links(entity_type: str, entity_id: str) -> list[ExternalLinkRead]:
    return [
        link
        for link in demo_data.links
        if link.entity_type == entity_type and link.entity_id == entity_id
    ]


@router.post("/{entity_type}/{entity_id}/links", response_model=ExternalLinkRead, status_code=201)
async def create_link(
    entity_type: str, entity_id: str, payload: ExternalLinkCreate
) -> ExternalLinkRead:
    return ExternalLinkRead(
        id="link_new",
        entity_type=entity_type,
        entity_id=entity_id,
        url=payload.url,
        title=payload.title,
        link_type=payload.link_type,
    )


@router.delete("/links/{link_id}", response_model=ApiMessage)
async def delete_link(link_id: str) -> ApiMessage:
    return ApiMessage(message=f"link {link_id} deleted")


@router.post("/links/preview", response_model=ExternalLinkRead)
async def preview_link(payload: ExternalLinkCreate) -> ExternalLinkRead:
    return ExternalLinkRead(
        id="preview",
        entity_type="link",
        entity_id="preview",
        url=payload.url,
        title=payload.title or payload.url,
        link_type=payload.link_type,
    )
